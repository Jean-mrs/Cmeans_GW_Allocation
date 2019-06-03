class OptimalK:
    """
    Obtain the optimal number of clusters a dataset should have using the gap statistic.
        Tibshirani, Walther, Hastie
        http://www.web.stanford.edu/~hastie/Papers/gap.pdf
    Example:
    >>> from sklearn.datasets.samples_generator import make_blobs
    >>> from gap_statistic import OptimalK
    >>> X, y = make_blobs(n_samples=int(1e5), n_features=2, centers=3, random_state=100)
    >>> optimalK = OptimalK(parallel_backend='joblib')
    >>> optimalK(X, cluster_array=[1,2,3,4,5])
    3
    """

    gap_df = None

    def __init__(
        self,
        n_jobs: int = -1,
        parallel_backend: str = "joblib",
        clusterer: Callable = None,
        clusterer_kwargs: dict = None,
    ) -> None:
        """
        Construct OptimalK to use n_jobs (multiprocessing using joblib, multiprocessing, or single core.
        if parallel_backend == 'rust' it will use all cores.
        :param n_jobs:
        :param parallel_backend:
        :param clusterer:
        :param clusterer_kwargs:
        """
        if clusterer is not None and parallel_backend == "rust":
            raise ValueError(
                "Cannot use 'rust' backend with a user defined clustering function, only KMeans"
                " is supported on the rust implementation"
            )
        self.parallel_backend = (
            parallel_backend
            if parallel_backend in ["joblib", "multiprocessing", "rust"]
            else None
        )
        self.n_jobs = n_jobs if 1 <= n_jobs <= cpu_count() else cpu_count()  # type: int
        self.n_jobs = 1 if parallel_backend is None else self.n_jobs
        self.clusterer = clusterer if clusterer is not None else kmeans2
        self.clusterer_kwargs = (
            clusterer_kwargs or dict()
            if clusterer is not None
            else dict(iter=10, minit="points")
        )

    def __call__(
        self,
        X: Union[pd.DataFrame, np.ndarray],
        n_refs: int = 3,
        cluster_array: Iterable[int] = (),
    ):
        """
        Calculates KMeans optimal K using Gap Statistic from Tibshirani, Walther, Hastie
        http://www.web.stanford.edu/~hastie/Papers/gap.pdf
        :param X - pandas dataframe or numpy array of data points of shape (n_samples, n_features)
        :param n_refs - int: Number of random reference data sets used as inertia reference to actual data.
        :param cluster_array - 1d iterable of integers; each representing n_clusters to try on the data.
        """

        # Convert the 1d array of n_clusters to try into an array
        # Raise error if values are less than 1 or larger than the unique sample in the set.
        cluster_array = np.array([x for x in cluster_array]).astype(int)
        if np.where(cluster_array < 1)[0].shape[0]:
            raise ValueError(
                "cluster_array contains values less than 1: {}".format(
                    cluster_array[np.where(cluster_array < 1)[0]]
                )
            )
        if cluster_array.shape[0] > X.shape[0]:
            raise ValueError(
                "The number of suggested clusters to try ({}) is larger than samples in dataset. ({})".format(
                    cluster_array.shape[0], X.shape[0]
                )
            )
        if not cluster_array.shape[0]:
            raise ValueError("The supplied cluster_array has no values.")

        # Array of resulting gaps.
        gap_df = pd.DataFrame({"n_clusters": [], "gap_value": []})

        # Define the compute engine; all methods take identical args and are generators.
        if self.parallel_backend == "joblib":
            engine = self._process_with_joblib
        elif self.parallel_backend == "multiprocessing":
            engine = self._process_with_multiprocessing
        elif self.parallel_backend == "rust":
            engine = self._process_with_rust
        else:
            engine = self._process_non_parallel

        # Calculate the gaps for each cluster count.
        for gap_calc_result in engine(X, n_refs, cluster_array):

            # Assign this loop's gap statistic to gaps
            gap_df = gap_df.append(
                {
                    "n_clusters": gap_calc_result.n_clusters,
                    "gap_value": gap_calc_result.gap_value,
                    "ref_dispersion_std": gap_calc_result.ref_dispersion_std,
                },
                ignore_index=True,
            )

        self.gap_df = gap_df.sort_values(by="n_clusters", ascending=True).reset_index(
            drop=True
        )
        return int(self.gap_df.loc[np.argmax(self.gap_df.gap_value.values)].n_clusters)

    @staticmethod
    def _calculate_dispersion(
        X: Union[pd.DataFrame, np.ndarray], labels: np.ndarray, centroids: np.ndarray
    ) -> float:
        """
        Calculate the dispersion between actual points and their assigned centroids
        """
        disp = np.sum(
            np.sum(
                [np.abs(inst - centroids[label]) ** 2 for inst, label in zip(X, labels)]
            )
        )
        return disp

    def _calculate_gap(
        self, X: Union[pd.DataFrame, np.ndarray], n_refs: int, n_clusters: int
    ) -> GapCalcResult:
        """
        Calculate the gap value of the given data, n_refs, and number of clusters.
        Return the resutling gap value and n_clusters
        """
        # Holder for reference dispersion results
        ref_dispersions = np.zeros(n_refs)

        # For n_references, generate random sample and perform kmeans getting resulting dispersion of each loop
        for i in range(n_refs):

            # Create new random reference set
            random_data = np.random.random_sample(size=X.shape)

            # Fit to it, getting the centroids and labels, and add to accumulated reference dispersions array.
            centroids, labels = self.clusterer(
                random_data, n_clusters, **self.clusterer_kwargs
            )  # type: Tuple[np.ndarray, np.ndarray]
            dispersion = self._calculate_dispersion(
                X=random_data, labels=labels, centroids=centroids
            )
            ref_dispersions[i] = dispersion

        # Fit cluster to original data and create dispersion calc.
        centroids, labels = self.clusterer(
            random_data, n_clusters, **self.clusterer_kwargs
        )  # type: Tuple[np.ndarray, np.ndarray]
        dispersion = self._calculate_dispersion(X=X, labels=labels, centroids=centroids)

        # Calculate gap statistic
        gap_value = np.mean(np.log(ref_dispersions)) - np.log(dispersion)

return GapCalcResult(gap_value, int(n_clusters), ref_dispersions.std())