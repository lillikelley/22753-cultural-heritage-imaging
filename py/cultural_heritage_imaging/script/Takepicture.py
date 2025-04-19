import PySpin
#import cv2

# print("PySpin Version:", PySpin.__version__)

system = PySpin.System.GetInstance()
cam_list = system.GetCameras()
cam = cam_list.GetByIndex(0)

try:
    cam.Init()

    cam.AcquisitionMode.SetValue(PySpin.AcquisitionMode_SingleFrame)

    cam.BeginAcquisition()

    image = cam.GetNextImage()

    if image.IsIncomplete():
            print(f'Image incomplete with status {image.GetImageStatus()}')
    else:
        #print(hasattr(image, "_pyspin_image"))
        print("Type of image object:", type(image))
        print("Attributes of image object:", dir(image))
        #image_converted = image.Convert(PySpin.PixelFormat_RGB8)
        numpy_array = image.GetNDArray()
            
        #cv2.imwrite("output_image.jpg", numpy_array)
        
    image.Release()
    print("Image saved successfully")
    cam.EndAcquisition()
    cam.DeInit()
    
except PySpin.SpinnakerException as ex:
    print("Spinnaker Exception:", ex)
    
finally:
    del cam
    cam_list.Clear()
    system.ReleaseInstance()    

    