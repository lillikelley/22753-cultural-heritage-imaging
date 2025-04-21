

import PySpin
#import cv2

system = PySpin.System.GetInstance()
cam_list = system.GetCameras()
num_cams = cam_list.GetSize()

if num_cams == 0:
    print("No cameras detected")
    cam_list.Clear()
    system.ReleaseInstance()
    system.exit()
else:
    print("Camera detected")
    cam = cam_list.GetByIndex(0)

try:
    cam.Init()
    
    cam.AcquisitionMode.SetValue(PySpin.AcquisitionMode_SingleFrame)

    cam.BeginAcquisition()

    image = cam.GetNextImage()

    if image.IsIncomplete():
            print(f'Image incomplete with status {image.GetImageStatus()}')
    else:
        filename = "Image1.jpg"
        image.Save(filename)
        print("Image saved successfully")

    image.Release()
    cam.EndAcquisition()
    cam.DeInit()
    
except PySpin.SpinnakerException as ex:
    print("Spinnaker Exception:", ex)
    
finally:
    del cam
    cam_list.Clear()
    system.ReleaseInstance()    

    