using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Threading;

namespace GAB.Client.Services
{
    public static class Retry
    {
        [DebuggerStepThrough]
        public static void Do(
            Action action,
            TimeSpan retryInterval,
            int retryCount = 3,
            Action firstExceptionAction = null)
        {
            Do<object>(() =>
            {
                action();
                return null;
            }, retryInterval, retryCount, firstExceptionAction);
        }

        [DebuggerStepThrough]
        public static T Do<T>(
            Func<T> action,
            TimeSpan retryInterval,
            int retryCount = 3,
            Action firstExceptionAction = null)
        {
            var exceptions = new List<Exception>();

            for (var retry = 0; retry < retryCount; retry++)
            {
                try
                {
                    return action();
                }
                catch (Exception ex)
                {
                    if (retry == 0 && firstExceptionAction != null)
                    {
                        firstExceptionAction();
                    }
                    else
                    {
                        exceptions.Add(ex);
                        Thread.Sleep(retryInterval);
                    }
                }
            }

            throw new AggregateException(exceptions);
        }


        [DebuggerStepThrough]
        public static void WaitUntil(
            Func<bool> action,
            TimeSpan maxInterval,
            TimeSpan retryInterval)
        {
            var start = DateTime.UtcNow;
            while (DateTime.UtcNow < (start + maxInterval))
            {
                if (action())
                {
                    return;
                }
                Thread.Sleep((int)retryInterval.TotalMilliseconds);
            }
        }
    }

}
