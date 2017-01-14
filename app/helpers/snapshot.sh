#!/bin/sh
rm -Rf /tmp/tag.jpeg
avconv -rtsp_transport tcp -i 'rtsp://192.168.1.10:554/user=admin_password=tlJwpbo6_channel=1_stream=0.sdp?real_stream--rtp-caching=100' -f image2 -vframes 1 -pix_fmt yuvj420p  /tmp/tag.jpg
#avconv -rtsp_transport tcp -i 'rtsp://192.168.1.10:554/user=admin_password=tlJwpbo6_channel=1_stream=0.sdp?real_stream--rtp-caching=100' -t 15 -an -f  mp4 -vcodec copy -y  /tmp/$today.mp4
