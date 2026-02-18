# -*- coding: utf-8 -*-
"""
MIT License

Copyright (c) 2018 Free TNT

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import time

# Ported from https://github.com/dirigeants/klasa/blob/master/src/lib/util/Stopwatch.js


class Stopwatch:
    """High-resolution elapsed-time timer.

    Measures elapsed wall-clock time using `time.perf_counter`. Supports
    start, stop, restart, and reset operations. Formats output in seconds,
    milliseconds, or microseconds depending on magnitude.
    """

    def __init__(self):
        """Start the stopwatch immediately upon construction."""
        self._start = time.perf_counter()
        self._end = None

    @property
    def duration(self) -> float:
        """Elapsed time in seconds.

        Returns:
            float: seconds since start (or between start and stop if stopped)
        """
        return self._end - self._start if self._end else time.perf_counter() - self._start

    @property
    def running(self) -> bool:
        """Whether the stopwatch is currently running.

        Returns:
            bool: True if the stopwatch has not been stopped
        """
        return not self._end

    def restart(self) -> "Stopwatch":
        """Reset start time to now and clear the stop time.

        Returns:
            Stopwatch: self, for chaining
        """
        self._start = time.perf_counter()
        self._end = None
        return self

    def reset(self) -> "Stopwatch":
        """Stop the stopwatch with zero elapsed time.

        Returns:
            Stopwatch: self, for chaining
        """
        self._start = time.perf_counter()
        self._end = self._start
        return self

    def start(self) -> "Stopwatch":
        """Resume the stopwatch if it is stopped.

        Returns:
            Stopwatch: self, for chaining
        """
        if not self.running:
            self._start = time.perf_counter() - self.duration
            self._end = None
        return self

    def stop(self) -> "Stopwatch":
        """Stop the stopwatch if it is running.

        Returns:
            Stopwatch: self, for chaining
        """
        if self.running:
            self._end = time.perf_counter()
        return self

    def __str__(self) -> str:
        """Format elapsed time as a human-readable string.

        Returns:
            str: elapsed time in s, ms, or μs depending on magnitude
        """
        time = self.duration * 1000
        if time >= 1000:
            return '{:.2f}s'.format(time / 1000)
        if time >= 1:
            return '{:.2f}ms'.format(time)
        return '{:.2f}μs'.format(time * 1000)
