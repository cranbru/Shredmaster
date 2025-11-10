    import os, secrets, time, threading, logging
    from abc import ABC, abstractmethod
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from typing import List, Optional, Tuple, Callable, Dict, Any


    class BaseShredder(ABC):
        """Base class for all shredding algorithms."""    
        def __init__(self, dry_run=False, logger=None):
            self.dry_run = dry_run
            self.logger = logger or logging.getLogger("ShredMaster")
            self.lock = threading.Lock()

        @abstractmethod
        def get_patterns(self) -> List[str]: ...
        @abstractmethod
        def get_name(self) -> str: ...

        def log(self, msg: str):
            with self.lock:
                self.logger.info(msg)

        def overwrite_file(self, filepath: str, secure_rename=False) -> bool:
            """Overwrites a file securely using the configured patterns."""
            try:
                if not os.path.exists(filepath):
                    self.log(f"File not found: {filepath}")
                    return False

                if self.dry_run:
                    self.log(f"[DRY RUN] Would shred {filepath}")
                    return True

                size = os.path.getsize(filepath)
                if size == 0:
                    os.remove(filepath)
                    return True

                with open(filepath, "r+b") as f:
                    for i, pattern in enumerate(self.get_patterns(), 1):
                        self.log(f"Pass {i}/{len(self.get_patterns())} on {filepath}")
                        self._write_pattern(f, size, pattern)

                if secure_rename:
                    filepath = self._secure_rename(filepath)
                os.remove(filepath)
                self.log(f"Successfully shredded: {filepath}")
                return True
            except Exception as e:
                self.logger.exception(f"Error shredding {filepath}: {e}")
                return False

        def _write_pattern(self, file_obj, size, pattern: str):
            block = 1024 * 1024
            file_obj.seek(0)
            remaining = size
            while remaining > 0:
                chunk_size = min(block, remaining)
                if pattern == "RANDOM":
                    data = secrets.token_bytes(chunk_size)
                else:
                    byte_val = int(pattern, 16)
                    data = bytes([byte_val]) * chunk_size
                file_obj.write(data)
                remaining -= chunk_size
            file_obj.flush()
            os.fsync(file_obj.fileno())

        def _secure_rename(self, filepath: str) -> str:
             """Rename file randomly before deletion."""
            dir_ = os.path.dirname(filepath)
            base = os.path.basename(filepath)
            randname = ''.join(secrets.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(len(base)))
            new_path = os.path.join(dir_, randname)
            counter = 0
            while os.path.exists(new_path):
                counter += 1
                new_path = os.path.join(dir_, f"{randname}_{counter}")
            os.rename(filepath, new_path)
            self.log(f"Renamed {filepath} -> {new_path}")
            return new_path


    class SimpleShredder(BaseShredder):
        def get_patterns(self): return ["00"]
        def get_name(self): return "Simple (1-pass)"


    class DoDShredder(BaseShredder):
        def get_patterns(self): return ["00", "FF", "RANDOM"]
        def get_name(self): return "DoD 5220.22-M (3-pass)"


    class GutmannShredder(BaseShredder):
        def get_patterns(self):
            specific = ["55", "AA", "92", "49", "24", "00", "11", "22", "33", "44",
                        "55", "66", "77", "88", "99", "AA", "BB", "CC", "DD", "EE", "FF"]
            return ["RANDOM"] * 4 + specific + ["RANDOM"] * 4
        def get_name(self): return "Gutmann (35-pass)"


    class CustomShredder(BaseShredder):
        def __init__(self, pattern, passes, dry_run=False, logger=None):
            super().__init__(dry_run, logger)
            self.pattern = pattern
            self.passes = passes

        def get_patterns(self):
            base = [p.strip() for p in self.pattern.split(',')] if self.pattern else ["RANDOM"]
            return [base[i % len(base)] for i in range(self.passes)]

        def get_name(self): return f"Custom ({self.passes}-pass)"


    class ShredMasterCore:
        """Core shredder logic managing threads, cancellation, and progress."""
        def __init__(self, logger=None):
            self.logger = logger or logging.getLogger("ShredMaster")
            self.cancel_flag = threading.Event()
            self.threads = 4
            self.algorithm = "simple"
            self.dry_run = False
            self.secure_rename = False
            self.custom_pattern = ""
            self.custom_passes = 3
            self._make_shredder()

        def _make_shredder(self):
            alg = self.algorithm
            if alg == "simple": self.shredder = SimpleShredder(self.dry_run, self.logger)
            elif alg == "DoD": self.shredder = DoDShredder(self.dry_run, self.logger)
            elif alg == "Gutmann": self.shredder = GutmannShredder(self.dry_run, self.logger)
            else:
                self.shredder = CustomShredder(self.custom_pattern, self.custom_passes, self.dry_run, self.logger)

        def update_settings(self, cfg: Dict[str, Any]):
            for k, v in cfg.items():
                setattr(self, k, v)
            self._make_shredder()

        def cancel(self): self.cancel_flag.set()

        def shred_files(self, files: List[str], progress: Optional[Callable[[int, int], None]] = None):
            start = time.time()
            success = 0
            total = len(files)
            self.logger.info(f"Starting shredding of {total} file(s) using {self.shredder.get_name()}")
            with ThreadPoolExecutor(max_workers=self.threads) as exe:
                fut_to_file = {exe.submit(self.shredder.overwrite_file, f, self.secure_rename): f for f in files}
                done = 0
                for fut in as_completed(fut_to_file):
                    if self.cancel_flag.is_set():
                        self.logger.info("Operation cancelled by user.")
                        break
                    try:
                        if fut.result(): success += 1
                    except Exception as e:
                        self.logger.exception(f"Failed to shred {fut_to_file[fut]}: {e}")
                    done += 1
                    if progress: progress(done, total)
            elapsed = time.time() - start
            self.logger.info(f"Done: {success}/{total} files in {elapsed:.2f}s")
            return success, total, elapsed

