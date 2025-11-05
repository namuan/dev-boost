import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

Command = str | Sequence[str]


@dataclass
class ProcessResult:
    """Standardized result for running external processes.

    Attributes:
        success: True if the process returned exit code 0.
        returncode: Process exit code (or -1 on failure before start).
        stdout: Captured standard output (empty string if not captured).
        stderr: Captured standard error (empty string if not captured).
        timed_out: Whether the process timed out.
        error: String description of the error if an exception occurred.
    """

    success: bool
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False
    error: str | None = None


def run_process(
    cmd: Command,
    *,
    timeout: float | None = None,
    shell: bool = False,
    text: bool = True,
    capture_output: bool = True,
    cwd: str | None = None,
    env: Mapping[str, str] | None = None,
    check: bool = False,
) -> ProcessResult:
    """Run a subprocess with unified handling and return a ProcessResult.

    This function centralizes subprocess execution for file_optimization engines, ensuring
    consistent timeouts, output capture, and error handling across the codebase.
    """
    try:
        kwargs = {
            "capture_output": capture_output,
            "text": text,
        }
        if timeout is not None:
            kwargs["timeout"] = timeout
        if shell:
            kwargs["shell"] = True
        if cwd is not None:
            kwargs["cwd"] = cwd
        if env is not None:
            kwargs["env"] = env

        result = subprocess.run(cmd, **kwargs)  # noqa: S603
        pr = ProcessResult(
            success=result.returncode == 0,
            returncode=result.returncode,
            stdout=result.stdout or "",
            stderr=result.stderr or "",
            timed_out=False,
            error=None,
        )
        if check and not pr.success:
            # Provide useful context to callers while preserving stdout/stderr
            err_text = pr.stderr or pr.stdout
            raise RuntimeError(f"Command failed ({pr.returncode}): {err_text}")
        return pr
    except subprocess.TimeoutExpired as e:
        return ProcessResult(
            success=False,
            returncode=-1,
            stdout=(getattr(e, "stdout", None) or ""),
            stderr=(getattr(e, "stderr", None) or str(e)),
            timed_out=True,
            error=str(e),
        )
    except (FileNotFoundError, PermissionError, subprocess.CalledProcessError) as e:
        return ProcessResult(
            success=False,
            returncode=-1,
            stdout="",
            stderr=str(e),
            timed_out=False,
            error=str(e),
        )
