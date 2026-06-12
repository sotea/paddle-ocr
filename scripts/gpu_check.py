import paddle

print("paddle version:", paddle.__version__)
print("compiled with cuda:", paddle.device.is_compiled_with_cuda())
print("gpu device count:", paddle.device.cuda.device_count())
try:
    print("device:", paddle.device.get_device())
except Exception as e:
    print("get_device error:", e)

paddle.utils.run_check()
