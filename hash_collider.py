# coding: utf-8
# python 3.6 x86_64

import sys
import multiprocessing as mp
import string
import hashlib
from time import time, sleep
from itertools import product


class ProcessScheduler:
    def __init__(self, nbr_process:int, func:'callable', qargs:list, static_args:tuple):
        self.nbr_process = nbr_process
        self.func = func
        self.qargs = self.init_queue(qargs)
        self.static_args = static_args

    def init_queue(self, liste:list):
        q = mp.Queue()
        for elem in liste:
            q.put(elem)
        return q

    def _worker(self, input, output):
        proc_name = mp.current_process().name
        func, qargs, static_args = input
        result = func(qargs, *static_args)
        output.put((proc_name, result, qargs))

    def run(self):
        processes = dict()
        output = mp.Queue()
        target, *others = self.static_args
        len_qargs = self.qargs.qsize()

        if self.nbr_process > len_qargs:
            print(f"[!] Error: number of processes is greater than qargs")
            sys.exit(0)

        print(f"[+] remaining {self.qargs.qsize()} / {len_qargs}  elements")

        for _ in range(self.nbr_process):
            input = (self.func, self.qargs.get(), self.static_args)
            p = mp.Process(target=self._worker, args=(input, output), daemon=True)
            print(f"[+] process '{p.name}' created with qargs '{input[1]}'")
            processes[p.name] = p

        print(f"[+] remaining {self.qargs.qsize()} / {len_qargs}  elements")

        for proc in processes.values():
            try:
                proc.start()
                print(f"[+] process '{proc.name}' started")
            except:
                print("[!] Error while process starting")
                print("[+] Try to kill all processes")
                for proc in processes.values():
                    self.stop_process(proc)
                    
        start = time()
        while True:
            if not output.empty():
                proc_name, result, qargs = output.get()

                if result:
                    print(f"[+] target {target} found by {proc_name} with qargs '{qargs}'")
                    print(f"[+] result -> {result}")
                    break
                else:
                    print(f"[+] target '{target}' not found by {proc_name} with qargs '{qargs}'")
                    self.stop_process(processes.pop(proc_name))

                    if not self.qargs.empty():
                        input = (self.func, self.qargs.get(), self.static_args)
                        p = mp.Process(target=self._worker, args=(input, output), daemon=True)
                        print(f"[+] process '{p.name}' created with qargs {input[1]}")
                        p.start()
                        print(f"[+] process '{p.name}' started")
                        processes[p.name] = p
                        print(f"[+] remaining {self.qargs.qsize()} / {len_qargs}  elements")
                    elif self.qargs.empty() and not processes:
                        print(f"[+] no result found for '{target}'")
                        break

        print(f"[+] Kill all processes")
        for proc in processes.values():
            self.stop_process(proc)

        print(f"total time -> {time() - start}")

    def stop_process(self, process):
        process.terminate()
        sleep(0.1)
        if not process.is_alive():
            print(f"[+] process '{process.name}' stopped")
        else:
            print(f"[-] process '{process.name}' don't stopped")


class Collision:
    algorythm = {
        "md5": hashlib.md5,
        "sha1": hashlib.sha1,
        "sha256": hashlib.sha256,
        "sha512": hashlib.sha512
    }

    def __init__(self, algo:str):
        self.hash = Collision.algorythm.get(algo)
        self.charset = [chr(_).encode() for _ in range(255)]

    def __call__(self, qargs:int, search:str):
        for i in product(self.charset, repeat=qargs):
            hexdigest = self.hash(b"".join(i)).hexdigest()
            if search in hexdigest:
                return b"".join(i)
        return False

