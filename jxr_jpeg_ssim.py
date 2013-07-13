#!/usr/bin/python
# Written by Josh Aas, Mozilla Corporation
# License: Do whatever you want with the code.

import os
import sys
import time
import test_utils

def main(argv):
  if len(argv) < 2:
  	print "First arg is a JPEG quality value to test (e.g. '75')."
  	print "Second arg is the path to an image to test (e.g. 'images/Lenna.jpg')."
  	print "Output is four lines: SSIM, JPEG-XR file size, JPEG file size, and JPEG-XR to JPEG file size ratio."
  	print "Output labels have no spaces so that a string split on a line produces the numeric result at index 1."
  	return

  jpeg_q = int(argv[1])
  png = argv[2]

  tmp_file_base = test_utils.path_for_file_in_tmp(png)

  jpg = tmp_file_base + str(jpeg_q) + ".jpg"
  test_utils.png_to_jpeg(png, jpeg_q, jpg)
  jpeg_file_size = os.path.getsize(jpg)
  jpg_png = jpg + ".png"
  test_utils.jpeg_to_png(jpg, jpg_png)
  jpeg_ssim = test_utils.ssim_float_for_images(png, jpg_png)
  os.remove(jpg)
  os.remove(jpg_png)

  jxr_ssim = 0.0
  jxr_file_size = 0
  q = 0.99
  while q >= 0.0:
    jxr = tmp_file_base + str(q) + ".jxr"
    test_utils.png_to_jxr(png, q, jxr)
    jxr_png = jxr + ".png"
    test_utils.jxr_to_png(jxr, jxr_png)
    ssim = test_utils.ssim_float_for_images(png, jxr_png)
    file_size = os.path.getsize(jxr)
    os.remove(jxr)
    os.remove(jxr_png)
    if ssim < jpeg_ssim:
      if jxr_file_size == 0:
        # Normally we require that the target format be capable of producing an
        # image at equal or greater quality than JPEG image being tested.
        # However, sometimes the quality metric will produce nearly equal values at
        # the high end and the target format can't match JPEG, particularly if
        # the image lacks much complexity. It can also happen, usually with the same
        # types of images, that the quality metric does not go down as requested
        # quality goes down. This can be a bug in the encoder or the quality metric.
        # In these troublesome cases, if the quality metric is close enough to JPEG
        # we'll simply charge the target image format with the highest file size that
        # it produces.
        if (jpeg_ssim - ssim) < 0.001:
          jxr_ssim = ssim
          jxr_file_size = file_size
        else:
          sys.stderr.write("Target format cannot match JPEG quality, aborting!\n")
          sys.exit(1)
      else:
        jxr_file_size = test_utils.file_size_interpolate(jxr_ssim, ssim, jpeg_ssim, jxr_file_size, file_size)
        # Note that jpeg_ssim must be updated *after* it's used for interpolation.
        jxr_ssim = jpeg_ssim # The JPEG-XR SSIM after interpolation is the same as the JPEG SSIM.
      break
    jxr_ssim = ssim
    jxr_file_size = file_size
    q -= 0.01

  ratio = float(jxr_file_size) / float(jpeg_file_size)

  print "SSIM: " + str(jpeg_ssim)[:5]
  print "JPEG-XR_File_Size_(kb): %.1f" % (float(jxr_file_size) / 1024.0)
  print "JPEG_File_Size_(kb): %.1f" % (float(jpeg_file_size) / 1024.0)
  print "JPEG-XR_to_JPEG_File_Size_Ratio: %.2f" % (ratio)

if __name__ == "__main__":
  main(sys.argv)