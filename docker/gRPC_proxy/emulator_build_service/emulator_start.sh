


setup_pulse_audio() {
  # We need pulse audio for the webrtc video bridge, let's configure it.
  mkdir -p /root/.config/pulse
  export PULSE_SERVER=unix:/tmp/pulse-socket
  pulseaudio -D -vvvv --log-time=1 --log-target=newfile:/tmp/pulseverbose.log --log-time=1 --exit-idle-time=-1
  tail -f /tmp/pulseverbose.log -n +1 | sed -u 's/^/pulse: /g' &
  pactl list || exit 1
}

forward_loggers() {
  mkdir /tmp/android-unknown
  mkfifo /tmp/android-unknown/kernel.log
  mkfifo /tmp/android-unknown/logcat.log
  echo "emulator: It is safe to ignore the warnings from tail. The files will come into existence soon."
  tail --retry -f /tmp/android-unknown/goldfish_rtc_0 | sed -u 's/^/video: /g' &
  #cat /tmp/android-unknown/kernel.log | sed -u 's/^/kernel: /g' &
  #cat /tmp/android-unknown/logcat.log | sed -u 's/^/logcat: /g' &
}

setup_pulse_audio
forward_loggers

# Forward adb port
/android/sdk/platform-tools/adb start-server &
socat -d tcp-listen:5555,reuseaddr,fork tcp:127.0.0.1:5557 &

# Forward gRPC for older emulator versions
socat -d tcp-listen:8554,reuseaddr,fork tcp:127.0.0.1:8556 &

# Start the emulator with the custom image
source /android/aosp/build/envsetup.sh
cd /android/aosp/ || exit 1
lunch sdk_x86_64-userdebug
emulator -no-window -ports "5556,5557" -grpc "8556" -skip-adb-auth -no-snapshot-save -wipe-data -logcat "*:V" -show-kernel -logcat-output "/tmp/android-unknown/logcat.log" -shell-serial "file:/tmp/android-unknown/kernel.log" -no-boot-anim -gpu swiftshader_indirect -turncfg "${TURN}" -qemu -append "panic=1"
