export const createApplicationDataLoaders = ({
  regions,
  jobs,
  errorMessage,
  regionUrl,
  jobUrl,
  REGIONS_CACHE_KEY,
  JOBS_CACHE_PREFIX,
  CACHE_TTL_MS,
  PREWARM_JOBS,
  PREWARM_REGION_LIMIT,
}) => {
  const jobsRequestMap = new Map();

  const canUseSessionStorage = () => typeof window !== "undefined" && !!window.sessionStorage;

  const readCache = (key) => {
    if (!canUseSessionStorage()) return null;
    try {
      const raw = window.sessionStorage.getItem(key);
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      if (!parsed || !parsed.timestamp || !("data" in parsed)) return null;
      if (Date.now() - parsed.timestamp > CACHE_TTL_MS) return null;
      return parsed.data;
    } catch {
      return null;
    }
  };

  const writeCache = (key, data) => {
    if (!canUseSessionStorage()) return;
    try {
      window.sessionStorage.setItem(
        key,
        JSON.stringify({
          timestamp: Date.now(),
          data,
        })
      );
    } catch {
      // Ignore cache write failures (e.g. private mode / quota)
    }
  };

  const fetchJobsByRegion = async (regionId, { silent = false } = {}) => {
    if (!regionId) return [];
    if (jobsRequestMap.has(regionId)) {
      return jobsRequestMap.get(regionId);
    }

    const request = (async () => {
      try {
        const response = await fetch(`${jobUrl}?region_id=${regionId}`);
        if (!response.ok) return [];
        const data = await response.json();
        writeCache(`${JOBS_CACHE_PREFIX}${regionId}`, data);
        return data;
      } catch (err) {
        if (!silent) throw err;
        return [];
      } finally {
        jobsRequestMap.delete(regionId);
      }
    })();

    jobsRequestMap.set(regionId, request);
    return request;
  };

  const prewarmJobs = async () => {
    if (!PREWARM_JOBS || !regions.value.length) return;
    const regionIds = regions.value
      .map((item) => Number(item.id))
      .filter((id) => Number.isInteger(id) && id > 0)
      .slice(0, PREWARM_REGION_LIMIT);
    if (!regionIds.length) return;

    await Promise.allSettled(
      regionIds.map(async (regionId) => {
        const cacheKey = `${JOBS_CACHE_PREFIX}${regionId}`;
        if (Array.isArray(readCache(cacheKey))) return;
        await fetchJobsByRegion(regionId, { silent: true });
      })
    );
  };

  const fetchRegions = async () => {
    const cachedRegions = readCache(REGIONS_CACHE_KEY);
    if (Array.isArray(cachedRegions)) {
      regions.value = cachedRegions;
      void prewarmJobs();
      return;
    }
    try {
      const response = await fetch(regionUrl);
      if (!response.ok) return;
      const data = await response.json();
      regions.value = data;
      writeCache(REGIONS_CACHE_KEY, data);
      void prewarmJobs();
    } catch (err) {
      errorMessage.value = "无法加载地区配置，请检查后端接口";
    }
  };

  const fetchJobs = async (regionId) => {
    if (!regionId) return;
    const cacheKey = `${JOBS_CACHE_PREFIX}${regionId}`;
    const cachedJobs = readCache(cacheKey);
    if (Array.isArray(cachedJobs)) {
      jobs.value = cachedJobs;
      return;
    }
    try {
      jobs.value = await fetchJobsByRegion(regionId);
    } catch (err) {
      errorMessage.value = "无法加载岗位列表，请检查后端接口";
    }
  };

  return {
    fetchRegions,
    fetchJobs,
  };
};
