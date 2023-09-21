from torch.utils.data import DataLoader
from geoseg.losses import *
from geoseg.datasets.uavid_dataset import *
from catalyst.contrib.nn import Lookahead
from catalyst import utils
from geoseg.models.MAResUNet import MAResUNet

# training hparam
# max_epoch = 45
max_epoch = 225
ignore_index = 255
train_batch_size = 8
val_batch_size = 8
lr = 6e-4
weight_decay = 0.01
backbone_lr = 6e-5
backbone_weight_decay = 0.01
accumulate_n = 1
num_classes = len(CLASSES)
classes = CLASSES

weights_name = "MAResUNet-r18_uavid_225"
weights_path = "model_weights/uavid/{}".format(weights_name)
test_weights_name = "MAResUNet-r18_uavid_225-v2"
#test_weights_name = "MAResUNet-r18_uavid_225-v1"
# test_weights_name = "MAResUNet-r18_uavid_225"
# test_weights_name = "last"
log_name = 'uavid/{}'.format(weights_name)
monitor = 'val_mIoU'
monitor_mode = 'max'
save_top_k = 3
save_last = False
check_val_every_n_epoch = 5
gpus = [0]
# gpus = 0

strategy = None
pretrained_ckpt_path = None
resume_ckpt_path = None
# 2023.1.10新增控制预训练权重参数
backbone_model_pretrain_path = None
# resume_ckpt_path = 'model_weights/potsdam/unetformer-r18-768crop-ms-e45/unetformer-r18-768crop-ms-e45.ckpt'
#  define the network
net = MAResUNet(num_classes=num_classes)

# define the loss
loss = UnetFormerLoss(ignore_index=ignore_index)
use_aux_loss = False

# train_dataset = UAVIDDataset(data_root='data/uavid/train_val', img_dir='images', mask_dir='masks',
#                              mode='train', mosaic_ratio=0.25, transform=train_aug, img_size=(1024, 1024))
train_dataset = UAVIDDataset(data_root='data/uavid/train', img_dir='images', mask_dir='masks',
                             mode='train', mosaic_ratio=0.25, transform=train_aug, img_size=(1024, 1024))

# val_dataset = UAVIDDataset(data_root='data/uavid/val', img_dir='images', mask_dir='masks', mode='val',
#                            mosaic_ratio=0.0, transform=val_aug, img_size=(1024, 1024))
val_dataset = UAVIDDataset(data_root='data/uavid/train_val', img_dir='images', mask_dir='masks', mode='val',
                           mosaic_ratio=0.0, transform=val_aug, img_size=(1024, 1024))

train_loader = DataLoader(dataset=train_dataset,
                          batch_size=train_batch_size,
                          num_workers=4,
                          pin_memory=True,
                          shuffle=True,
                          drop_last=False)

val_loader = DataLoader(dataset=val_dataset,
                        batch_size=val_batch_size,
                        num_workers=4,
                        shuffle=False,
                        pin_memory=True,
                        drop_last=False)

# define the optimizer
layerwise_params = {"backbone.*": dict(lr=backbone_lr, weight_decay=backbone_weight_decay)}
net_params = utils.process_model_params(net, layerwise_params=layerwise_params)
base_optimizer = torch.optim.AdamW(net_params, lr=lr, weight_decay=weight_decay)
optimizer = Lookahead(base_optimizer)
# lr_scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=max_epoch)
lr_scheduler = torch.optim.lr_scheduler.CosineAnnealingWarmRestarts(optimizer, T_0=15, T_mult=2)

