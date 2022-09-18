from settings.train_settings import *
from engine.trainer import BaseTrainer
import torch.multiprocessing as mp
import torch.distributed as dist
from engine.ddp_train import train
os.environ['MASTER_ADDR'] = 'localhost'
os.environ['MASTER_PORT'] = '12355'

if __name__ == '__main__':
    if os.environ['RANK'] == 0:
        args = ArgParser(True).get_args()
    else:
        args = ArgParser(False).get_args()

    local_rank = int(os.environ["LOCAL_RANK"])
    rank = local_rank + args.node_rank * args.nnodes
    store = 'file://' + os.path.join(args.model_dir, 'share')
    print(store)
    print(local_rank)
    print(store)
    print(rank)
    # dist.init_process_group("nvcc", init_method=store, rank=rank, world_size=args.nnodes * args.nproc_per_node)
    dist.init_process_group('nccl', init_method="tcp://localhost:12355")
    print(os.environ)
    trainer = BaseTrainer(args, local_rank)
    trainer.train_model()
