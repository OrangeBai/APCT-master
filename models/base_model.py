import importlib
import os
from collections import OrderedDict
import torch.nn as nn
from dataloader.base import set_mean_sed
import torch


class BaseModel(nn.Module):
    # TODO Record epoch info
    def __init__(self, args):
        super(BaseModel, self).__init__()
        self.set_up_kwargs = {'batch_norm': args.batch_norm, 'activation': args.activation}
        self.norm_layer = NormalizeLayer(*set_mean_sed(args))

    def forward(self, x):
        pass

    def save_model(self, path, name=None):
        if not name:
            model_path = os.path.join(path, 'weights.pth')
        else:
            model_path = os.path.join(path, 'weights_{}.pth'.format(name))
        torch.save(self.state_dict(), model_path)
        return

    def load_model(self, path, name=None):
        if not name:
            model_path = os.path.join(path, 'weights.pth')
        else:
            model_path = os.path.join(path, 'weights_{}.pth'.format(name))
        self.load_weights(torch.load(model_path))

        print('Loading model from {}'.format(model_path))
        return

    def load_weights(self, state_dict):
        new_dict = OrderedDict()
        for (k1, v1), (k2, v2) in zip(self.state_dict().items(), state_dict.items()):
            if v1.shape == v2.shape:
                new_dict[k1] = v2
            else:
                raise KeyError
        self.load_state_dict(new_dict)


def build_model(args):
    """Import the module "model/[model_name]_model.py"."""
    model = None
    if args.model_type == 'dnn':
        model_file_name = "models." + args.model_type
        modules = importlib.import_module(model_file_name)
        model = modules.__dict__['DNN'](args)
    elif args.model_type == 'mini':
        model_file_name = "models." + "mini"
        modules = importlib.import_module(model_file_name)
        model = modules.set_model(args)
    elif args.model_type == 'net':
        model_file_name = "models." + "net"
        modules = importlib.import_module(model_file_name)
        for k, val in modules.__dict__.items():
            if k.lower() == args.net.lower():
                model = val(args)
    else:
        raise NameError

    if model is None:
        print("In %s.py, there should be a subclass of BaseModel with class name that matches %s in lowercase." % (
            model_file_name, args.net))
        exit(0)
    else:
        return model


class NormalizeLayer(torch.nn.Module):
    """Standardize the channels of a batch of images by subtracting the dataset mean
      and dividing by the dataset standard deviation.

      In order to certify radii in original coordinates rather than standardized coordinates, we
      add the Gaussian noise _before_ standardizing, which is why we have standardization be the first
      layer of the classifier rather than as a part of preprocessing as is typical.
      """

    def __init__(self, means, sds):
        """
        :param means: the channel means
        :param sds: the channel standard deviations
        """
        super(NormalizeLayer, self).__init__()
        self.means = torch.tensor(means).cuda()
        self.sds = torch.tensor(sds).cuda()

    def forward(self, input: torch.tensor):
        (batch_size, num_channels, height, width) = input.shape
        means = self.means.repeat((batch_size, height, width, 1)).permute(0, 3, 1, 2)
        sds = self.sds.repeat((batch_size, height, width, 1)).permute(0, 3, 1, 2)
        return (input - means) / sds