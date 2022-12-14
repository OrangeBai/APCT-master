from core.DualNet import DualNet
from models.net.resnet import Bottleneck
from core.smooth_core import *


class SCRFP(Smooth):
    """A smoothed classifier g """

    # to abstain, Smooth returns this int
    ABSTAIN = -1

    def __init__(self, base_classifier, args=None):
        """
        :param base_classifier: maps from [batch x channel x height x width] to [batch x num_classes]
        """
        super().__init__(base_classifier, args)
        self.dual_net = DualNet(base_classifier, args)

    def _sample_noise(self, x: torch.tensor, num: int, batch_size) -> np.ndarray:
        """ Sample the base classifier's prediction under noisy corruptions of the input x.

        :param x: the input [channel x width x height]
        :param num: number of samples to collect
        :param batch_size:
        :return: an ndarray[int] of length num_classes containing the per-class counts
        """
        self.dual_net.eval()
        with torch.no_grad():
            counts = np.zeros(self.num_classes, dtype=int)
            for _ in range(ceil(num / batch_size)):
                this_batch_size = min(batch_size, num)
                num -= this_batch_size

                batch = x.repeat((this_batch_size + 1, 1, 1, 1))
                n = torch.randn_like(x).to(x.device) * self.sigma
                n[0] = 0
                # batch = self.reverse_noise(batch)
                predictions = self.dual_net.predict(batch+n, 0.0, self.args.eta_float)[1:]
                counts += self._count_arr(predictions.argmax(1).cpu().numpy(), self.num_classes)
            return counts
