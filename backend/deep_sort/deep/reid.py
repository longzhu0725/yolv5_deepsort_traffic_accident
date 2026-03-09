import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import os


class BasicBlock(nn.Module):
    def __init__(self, in_planes, planes, stride=1):
        super(BasicBlock, self).__init__()
        self.conv1 = nn.Conv2d(in_planes, planes, kernel_size=3, stride=stride, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(planes)
        self.conv2 = nn.Conv2d(planes, planes, kernel_size=3, stride=1, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(planes)
        
        self.downsample = nn.Sequential()
        if stride != 1 or in_planes != planes:
            self.downsample = nn.Sequential(
                nn.Conv2d(in_planes, planes, kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm2d(planes)
            )
    
    def forward(self, x):
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        out += self.downsample(x)
        out = F.relu(out)
        return out


class ResNet(nn.Module):
    def __init__(self, block, num_blocks, num_classes=751):
        super(ResNet, self).__init__()
        self.in_planes = 64
        
        self.conv = nn.Sequential(
            nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1, bias=True),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True)
        )
        self.layer1 = self._make_layer(block, 64, num_blocks[0], stride=1)
        self.layer2 = self._make_layer(block, 128, num_blocks[1], stride=2)
        self.layer3 = self._make_layer(block, 256, num_blocks[2], stride=2)
        self.layer4 = self._make_layer(block, 512, num_blocks[3], stride=2)
        self.classifier = nn.Sequential(
            nn.Linear(512, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(256, num_classes)
        )
    
    def _make_layer(self, block, planes, num_blocks, stride):
        strides = [stride] + [1] * (num_blocks - 1)
        layers = []
        for stride in strides:
            layers.append(block(self.in_planes, planes, stride))
            self.in_planes = planes
        return nn.Sequential(*layers)
    
    def forward(self, x):
        out = self.conv(x)
        out = self.layer1(out)
        out = self.layer2(out)
        out = self.layer3(out)
        out = self.layer4(out)
        out = F.adaptive_avg_pool2d(out, (1, 1))
        out = out.view(out.size(0), -1)
        out = self.classifier(out)
        return out


class Extractor:
    def __init__(self, model_path=None, use_cuda=True):
        self.device = torch.device('cuda' if use_cuda and torch.cuda.is_available() else 'cpu')
        self.model = ResNet(BasicBlock, [2, 2, 2, 2], num_classes=751)
        self.model.to(self.device)
        self.model.eval()
        
        if model_path and os.path.exists(model_path):
            try:
                checkpoint = torch.load(model_path, map_location=self.device)
                if isinstance(checkpoint, dict) and 'net_dict' in checkpoint:
                    state_dict = checkpoint['net_dict']
                elif isinstance(checkpoint, dict):
                    if 'state_dict' in checkpoint:
                        state_dict = checkpoint['state_dict']
                    elif 'model' in checkpoint:
                        state_dict = checkpoint['model']
                    else:
                        state_dict = checkpoint
                else:
                    state_dict = checkpoint
                
                new_state_dict = {}
                for k, v in state_dict.items():
                    name = k.replace('module.', '') if k.startswith('module.') else k
                    new_state_dict[name] = v
                
                self.model.load_state_dict(new_state_dict, strict=True)
                print(f'ReID模型权重加载成功: {model_path}')
            except Exception as e:
                print(f'ReID模型权重加载失败: {e}')
                import traceback
                traceback.print_exc()
        else:
            print(f'ReID模型文件不存在: {model_path}')
            print('使用随机初始化的ReID模型')
    
    def __call__(self, img_crops):
        if len(img_crops) == 0:
            return np.array([])
        
        features = []
        with torch.no_grad():
            for crop in img_crops:
                if crop.size == 0:
                    features.append(np.zeros(256))
                    continue
                
                crop = self._preprocess(crop)
                crop = crop.to(self.device)
                feat = self.model(crop)
                feat = feat[:, :256]
                feat = feat.cpu().numpy().flatten()
                feat = feat / (np.linalg.norm(feat) + 1e-8)
                features.append(feat)
        
        return np.array(features)
    
    def _preprocess(self, img):
        import cv2
        img = cv2.resize(img, (64, 128))
        img = img.astype(np.float32) / 255.0
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        img = (img - mean) / std
        img = img.transpose(2, 0, 1)
        img = torch.from_numpy(img).unsqueeze(0)
        return img
