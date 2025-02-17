import sys
import os
import logging
from .buildtree import check_buildtree, BuildTree
from .subp import sys_memory_size

from .preprocess import load_plugins
load_plugins()

def build_lmdb(tree, path, config):
    from .preprocess import get_preprocess_method
    if 'input' not in config:
        return
    data_config = config['input']
    preprocess = get_preprocess_method(data_config['preprocess'])
    preprocess(tree, config)

def main():
    logging.basicConfig(
        level=logging.INFO,
        format='[%(levelname)s %(filename)s:%(lineno)d] %(message)s')

    if not check_buildtree():
        sys.exit(1)
    import argparse
    parser = argparse.ArgumentParser(description='tpu-perf benchmark tool')
    BuildTree.add_arguments(parser)
    args = parser.parse_args()
    tree = BuildTree(os.path.abspath('.'), args)

    mem_size = sys_memory_size()
    max_workers = max(1, int(mem_size / 1024 / 1024 / 7))
    num_workers = 4
    if num_workers > max_workers:
        num_workers = max_workers
        logging.info(
            f'System memory {mem_size}, using {num_workers} workers.')

    # Synchronous invoking for debug
    #
    #for path, config in tree.walk():
    #    build_lmdb(tree, path, config)
    #return

    from concurrent.futures import ThreadPoolExecutor, as_completed
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []

        for path, config in tree.walk():
            f = executor.submit(build_lmdb, tree, path, config)
            futures.append(f)

        for f in as_completed(futures):
            err = f.exception()
            if err:
                logging.error(f'Quit because of exception, {err}')
                os._exit(-1)

if __name__ == '__main__':
    main()
