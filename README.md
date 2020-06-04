oracle-weather
---------------

天气数据上链和链天气数据更新订阅服务，也即一个简单的oracle demo  
> demo中仅上传北京市区天气，15分钟拉取一次高德天气数据，上传到链上，若拉取的高德天气数据未更新，则上传失败。


## 依赖
1. [python-sdk](https://github.com/Cocos-BCX/Python-Middleware)

2. 高德天气数据

## 运行  
``` text  
./start_d.sh
或
python3 main.py
```


