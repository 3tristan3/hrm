// 任务并发执行器：按并发上限调度任务并在首个失败时中断。
export const runTasksWithConcurrency = async (tasks, concurrency = 2) => {
  if (!Array.isArray(tasks) || tasks.length === 0) return;
  const workerCount = Math.max(
    1,
    Math.min(Number(concurrency) || 1, tasks.length)
  );
  let index = 0;
  let firstError = null;

  const worker = async () => {
    while (true) {
      if (firstError) return;
      const taskIndex = index;
      index += 1;
      if (taskIndex >= tasks.length) return;
      try {
        await tasks[taskIndex]();
      } catch (err) {
        firstError = err;
        return;
      }
    }
  };

  await Promise.all(Array.from({ length: workerCount }, () => worker()));
  if (firstError) throw firstError;
};
