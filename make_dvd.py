#!/usr/bin/env python

#import collections
import argparse
import datetime
import json
import os
#import subprocess
import sys

def sec_to_timestamp(sec):
	h = sec / 3600
	m = (sec / 60) - (h * 60)
	s = sec % 60
	#timestamp = "%02d:%02d:%02d" % (h, m, s)
	timestamp = "%02d:%02d:0.0" % (h, m)
	return timestamp

def exec_cmd(cmd):
	#Proc = collections.namedtuple('Proc', ['stdout', 'stderr', 'exitcode'])
	exitcode = 0
	if isinstance(cmd, list):
		cmd_str = " ".join(cmd)
	else:
		cmd_str = cmd
	print "Executing: %s" % cmd_str

	process = subprocess.Popen(cmd_str, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
	while True:
		output = process.stdout.readline()
		if output == '' and process.poll() is not None:
			break
		if output:
			print output.strip()
	exitcode = process.poll()
	return exitcode
		
	#out, err = process.communicate()
	#retval = process.returncode
	#return Proc(stdout=out, stderr=err, exitcode=retval)


parser = argparse.ArgumentParser()
parser.add_argument("input", help="input video file", action="store", type=str)
parser.add_argument('-f','--force', help='Reuse existing files', action='store_true', default=False)
parser.add_argument("-t", "--title", help="DVD title", dest="title", action="store", type=str, required=True)
parser.add_argument("-a", "--action", help="Action to take", dest="action", action="store", type=str,
		    choices=["convert", "inspect"], default="convert")
args = parser.parse_args()

print args

input_path = os.path.abspath(args.input)
basedir = os.path.dirname(input_path)
input_basename = os.path.basename(input_path)
input_filename, input_ext = os.path.splitext(input_basename)
output_dir = os.path.join(basedir, "dvd")
ffmpeg_output_file = os.path.join(output_dir, input_filename + ".mpg").replace(" ", "_")
ffmpeg_output_file_log = ffmpeg_output_file + ".vlog"
dvdauthor_file_path = os.path.join(output_dir, "dvdauthor.xml")
dvdauthor_output_dir = os.path.join(output_dir, "dvd")
iso_path = os.path.join(basedir, "dvd.iso")

iso_title = args.title[:32]
if iso_title != args.title:
	print "WARNING: Changed ISO title from '%s' to '%s'" % (args.title, iso_title)

if not os.path.exists(input_path):
	print "Input File Not Found! %s" % input_path
	sys.exit(1)

if args.action == "convert" and not os.path.exists(output_dir):
	os.makedirs(output_dir)
elif args.action == "convert" and os.listdir(output_dir) and not args.force:
	print "Output directory is not empty!"
	sys.exit(1)

# Probe input video data
input_video_data_str = os.popen("ffprobe -show_format -show_streams -of json '%s'" % input_path).read().strip()
#print input_video_data_str
input_video_data = json.loads(input_video_data_str)
print json.dumps(input_video_data, sort_keys=True, indent=4)


# Get duration
duration_str = input_video_data["format"]["duration"]
duration_sec = int(round(float(duration_str)))
print duration_sec

# Generate chapter timestamp list
chapters = []
for s in xrange(300,duration_sec,300):
	timestamp = sec_to_timestamp(s)
	chapters.append(timestamp)

print chapters

# Find english audio stream
audio_stream = None
for stream in input_video_data.get("streams"):
	_stream_type = stream.get("codec_type")
	if _stream_type != "audio":
		continue
	_stream_tags = stream.get("tags")
	if _stream_tags:
		_stream_lang = _stream_tags.get("language")
	else:
		_stream_lang = None
	if _stream_lang:
		if "eng" in _stream_lang or "Eng" in _stream_lang:
			audio_stream = stream.get("index") - 1

if audio_stream != None:
	audio_stream_map = "0:a:%s" % audio_stream
else:
	audio_stream_map = "0:a"

# Fix video scale
# ffmpeg -i "/home/treydock/Downloads/complete/Cloudy_with_a_Chance_of_Meatballs/d-wmaaf-1080-rr.mkv" -target ntsc-dvd -g 18 -b 6000000 -maxrate 9000000 -minrate 0 -bufsize 1835008 -packetsize 2048 -muxrate 10080000 -b:a 448000 -aspect 16:9 -s 720x480 -vf scale=720:364,pad=720:480:0:58:black -b 5999k -b:a 320k -y -mbd rd -trellis 2 -cmp 2 -subcmp 2 -threads 4 -map 0:v:0 -map 0:a -pass 1 -passlogfile "/home/treydock/Downloads/complete/Cloudy_with_a_Chance_of_Meatballs/dvd/1.d-wmaaf-1080-rr.mkv.mpg.vlog" "/dev/null"

for stream in input_video_data.get("streams"):
	_stream_type = stream.get("codec_type")
	if _stream_type != "video":
		continue
	video_stream = stream

video_height = video_stream.get("height")
video_width = video_stream.get("width")
video_aspect_ratio = video_stream.get("display_aspect_ratio")

v_ar = video_aspect_ratio.split(":")
v_ar_w = int(v_ar[0])
v_ar_h = int(v_ar[1])

print "VIDEO SIZE: %d x %d" % (video_width, video_height)
print "VIDEO ASPECT = %d/%d" % (v_ar_w, v_ar_h)
source_ar = v_ar_w / v_ar_h

target_ar_w = 16
target_ar_h = 9
target_ar = target_ar_w / target_ar_h

if source_ar > target_ar:
	print "Height needs to be padded"
	new_video_w = 720
	new_video_h = int(float(new_video_w) * (float(video_height) / float(video_width)))
	padding = 480 - new_video_h
	video_x = 0
	video_y = int(padding / 2)
	scale = "-vf scale=%d:%d,pad=720:480:%d:%d:black" % (new_video_w, new_video_h, video_x, video_y)
#	scale = "-vf scale=%s:%s" % (new_video_w, new_video_h)
elif source_ar < target_ar:
	print "Width needs to be padded"
	new_video_h = 480
	new_video_w = int(float(new_video_h) * (float(video_width) / float(video_height)))
	padding = 720 - new_video_w
	video_x = 0
	video_y = int(padding / 2)
	scale = "-vf scale=%d:%d,pad=720:480:%d:%d:black" % (new_video_w, new_video_h, video_x, video_y)
#	scale = "-vf scale=%s:%s" % (new_video_w, new_video_h)
else:
	print "No padding needed"
	scale = ""

#scale = "scale=-1:480,pad=:ih:(ow-iw)/2"
scale = "-vf \"scale=w=720:h=480:force_original_aspect_ratio=1,pad=720:480:(ow-iw)/2:(oh-ih)/2\""
print "SCALE: %s" % scale

# Caculate expected size and optimal bit rate
#expected_video_size = (duration_sec * (6000 / 1000)) / 8
#expected_audio_size = (duration_sec * (448 / 1000)) / 8
expected_video_size = (duration_sec * (6000 * 1000))
expected_video_size_mb = round((expected_video_size / 1024**2) / 8)
expected_audio_size = (duration_sec * (1536 * 1000))
expected_audio_size_mb = round((expected_audio_size / 1024**2) / 8)
expected_size = expected_video_size + expected_audio_size
expected_size_mb = expected_video_size_mb + expected_audio_size_mb
#expected_size_mb = round(expected_video_size) + round(expected_audio_size)
print "Expected Video Size: %s MB | Expected Audio Size: %s MB | Expected Size: %s MB" % (expected_video_size_mb, expected_audio_size_mb, expected_size_mb)
#print "Expected Size: %s MB" % expected_size_mb

max_size = 4.6 * 1024**3 * 8
max_video_size = max_size - expected_audio_size

max_video_bitrate = round(max_video_size / duration_sec)
print "Max Video Bitrate: %s b/s" % max_video_bitrate

v_bits = 3450000 * duration_sec
v_mb = round((v_bits / 1024**2) / 8)

print "Bitrate: %s" % 	v_mb

#while

optimal_bitrate_kb = int(((8.0 * (4000.0 * 1000.0)) / float(duration_sec)) * 0.9)
print "Optimal Bitrate: %s kb/s" % optimal_bitrate_kb
optimal_bitrate = 1000 * optimal_bitrate_kb

print "%s - CURRENT BIT RATE" % int(float(input_video_data["format"]["bit_rate"]))
max_size = 4.6 * 1024**3 * 8
max_bitrate = int(max_size) / duration_sec
print "%s - MAX BIT RATE" % int(max_bitrate)
print "MAX BITS: %s" % max_size

# Get file size
#ffmpeg_output_file_size = os.path.getsize(ffmpeg_output_file)
#ffmpeg_output_file_size_mb = round(ffmpeg_output_file_size / 1000**2)
#print "OUTPUT FILE SIZE: %s MB" % ffmpeg_output_file_size_mb

if args.action == "inspect":
	sys.exit(0)

# Convert to mpeg2 / ntsc-dvd
#/usr/bin/ffmpeg -i /home/treydock/Downloads/complete/Jurassic.World.2015.BDRip.x264-SPARKS/Jurassic.World.2015.BDRip.x264-SPARKS.mkv -vf scale=720:426,fifo,pad=720:480:0:28:0x000000 -y -target ntsc-dvd -acodec ac3 -sn -g 12 -bf 2 -strict 1 -ac 2 -s 720x480 -threads 4 -trellis 1 -mbd 2 -b 3905k -b:a 224k -aspect 16:9 /home/treydock/Downloads/complete/Jurassic.World.2015.BDRip.x264-SPARKS/dvd2/movie/movie_01_01.mpg

ffmpeg_pass1_cmd = [
	"ffmpeg", "-i", "'%s'" % input_path, "-target", "ntsc-dvd", "-threads", "12", "-y",
#  "-hwaccel", "auto",
	"-aspect", "16:9", "-s", "720x480",
	"-map", "0:v", "-map", audio_stream_map,
	#"-b:v", '3400000', '-maxrate:v', '8000000',
	#"-b 4000000 -maxrate 9000000", #TODO
	scale,
	"-pass 1", "-an",
	"-passlogfile", "'%s'" % ffmpeg_output_file_log,
	"/dev/null"
]
ffmpeg_pass1_cmd_str = " ".join(ffmpeg_pass1_cmd)
#if os.path.exists("%s-0.log" % ffmpeg_output_file_log) and args.force:
#  print "USING: %s" % ffmpeg_output_file_log
#else:
#  print "EXECUTING: %s" % ffmpeg_pass1_cmd_str
#  ffmpeg_pass1_exitcode = os.system(ffmpeg_pass1_cmd_str)
#  if ffmpeg_pass1_exitcode != 0:
#	  print "Failed during execution of ffmpeg pass 1"
#	  sys.exit(1)

ffmpeg_pass2_cmd = [
	"ffmpeg", "-i", "'%s'" % input_path, "-target", "ntsc-dvd", "-threads", "12", "-y",
#  "-hwaccel", "auto",
	"-aspect", "16:9", "-s", "720x480",
	"-map", "0:v", "-map", audio_stream_map,
	#"-b:v", '3400000', '-maxrate:v', '8000000',
	#"-b 4000000 -maxrate 9000000", #TODO
	scale,
	"-pass 2",
	"-passlogfile", "'%s'" % ffmpeg_output_file_log,
	"'%s'" % ffmpeg_output_file
]
ffmpeg_pass2_cmd_str = " ".join(ffmpeg_pass2_cmd)
#print "EXECUTING: %s" % ffmpeg_pass2_cmd_str
#ffmpeg_pass2_exitcode = os.system(ffmpeg_pass2_cmd_str)
ffmpeg_pass2_exitcode = 0
if ffmpeg_pass2_exitcode != 0:
	print "Failed during execution of ffmpeg pass 2"
	sys.exit(1)
else:
	print "Completed ffmpeg"

ffmpeg_cmd = [
	"ffmpeg", "-i", "'%s'" % input_path, "-target", "ntsc-dvd", "-threads", "12", "-y",
#  "-hwaccel", "auto",
	"-aspect", "16:9", "-s", "720x480",
	"-map", "0:v", "-map", audio_stream_map,
	#"-b:v", '3400000', '-maxrate:v', '8000000',
	#"-b 4000000 -maxrate 9000000", #TODO
	scale,
	"'%s'" % ffmpeg_output_file
]
if os.path.exists(ffmpeg_output_file) and args.force:
	print "USING: %s" % ffmpeg_output_file
else:
	ffmpeg_cmd_str = " ".join(ffmpeg_cmd)
	print "EXECUTING: %s" % ffmpeg_cmd_str
	ffmpeg_exitcode = os.system(ffmpeg_cmd_str)
	if ffmpeg_exitcode != 0:
		print "Failed during execution of ffmpeg"
		sys.exit(1)
	else:
		print "Completed ffmpeg"

# Generate dvdauthor.xml
dvdauthor_content = '<?xml version="1.0" encoding="UTF-8"?> \
\n<dvdauthor> \
\n  <vmgm> \
\n    <!--First Play-->\
\n    <fpc>jump menu entry title;</fpc>\
\n    <menus>\
\n      <video format="ntsc" aspect="4:3" resolution="720xfull"/>\
\n      <!--copy-n-paste?-->\
\n      <subpicture lang="EN"/>\
\n      <pgc entry="title">\
\n        <pre>g2 = 0; jump title 1;</pre>\
\n      </pgc>\
\n    </menus>\
\n  </vmgm>\
\n  <titleset>\
\n    <menus>\
\n      <video format="ntsc" aspect="16:9" widescreen="nopanscan"/>\
\n      <subpicture>\
\n        <stream id="0" mode="widescreen"/>\
\n        <stream id="1" mode="letterbox"/>\
\n      </subpicture>\
\n    </menus>\
\n    <titles>\
\n      <video format="ntsc" aspect="16:9" widescreen="nopanscan"/>\
\n      <pgc>\
\n        <vob file="' + ffmpeg_output_file + '" chapters="' + ", ".join(chapters) + '"/> \
\n        <post>g2 = 0; jump title 1;</post> \
\n      </pgc>\
\n    </titles>\
\n  </titleset>\
\n</dvdauthor>'

print dvdauthor_content

dvdauthor_file = open(dvdauthor_file_path, 'w')
dvdauthor_file.write(dvdauthor_content)
dvdauthor_file.close()

#dvdauthor_exitcode = exec_cmd(["dvdauthor", "-o", dvdauthor_output_dir, "-x", dvdauthor_file_path])
dvdauthor_exitcode = os.system("dvdauthor -o %s -x %s" % (dvdauthor_output_dir, dvdauthor_file_path))

if dvdauthor_exitcode != 0:
	print "Failed during execution of dvdauthor"
	sys.exit(1)
else:
	print "Completed dvdauthor"

# Generate final ISO file
#genisoimage_exitcode = exec_cmd("genisoimage -V '%s' -dvd-video '%s' > %s" % (dvd_title, dvdauthor_output_dir, iso_path))
genisoimage_exitcode = os.system("genisoimage -V '%s' -dvd-video '%s' > %s" % (iso_title, dvdauthor_output_dir, iso_path))


