FROM debian:10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libc6 libdbus-1-3 libfontconfig1 libgcc1 \
    libpulse0 libtinfo5 libx11-6 libxcb1 libxdamage1 \
    libnss3 libxcomposite1 libxcursor1 libxi6 \
    libxext6 libxfixes3 zlib1g libgl1 pulseaudio pulseaudio-utils socat \
    iputils-ping curl ca-certificates wget unzip procps rsync net-tools

################################
# Install Java
################################
RUN mkdir -p /usr/local/jdk-21
WORKDIR /usr/local/jdk-21
RUN wget https://download.java.net/java/GA/jdk21.0.1/415e3f918a1f4062a0074a2794853d0d/12/GPL/openjdk-21.0.1_linux-x64_bin.tar.gz
RUN tar -xf openjdk-21.0.1_linux-x64_bin.tar.gz
RUN mv jdk-21.0.1/* ./
ENV JAVA_HOME=/usr/local/jdk-21
ENV PATH=$JAVA_HOME/bin:$PATH

################################
# Install pulse audio default config
################################
COPY ./emulator_build_service/default.pa /etc/pulse/default.pa

################################
# Install Android SDK and tools
################################
RUN mkdir -p /android/sdk/cmdline-tools/latest && mkdir -p /android/sdk/avd && mkdir -p /android/sdk/platforms  \
    && mkdir -p /android/sdk/platforms && mkdir -p /android/sdk/platform-tools && mkdir -p /android/sdk/system-images  \
    && mkdir /android/tmp && mkdir -p /android/user_home/
WORKDIR /android
RUN wget https://dl.google.com/android/repository/commandlinetools-linux-10406996_latest.zip
RUN wget https://dl.google.com/android/repository/platform-tools-latest-linux.zip
RUN unzip commandlinetools-linux-10406996_latest.zip -d /android/tmp
RUN unzip platform-tools-latest-linux.zip -d /android/sdk/
RUN mv /android/tmp/cmdline-tools/* /android/sdk/cmdline-tools/latest/
ENV ANDROID_HOME=/android/sdk
ENV ANDROID_SDK_ROOT=/android/sdk
ENV ANDROID_AVD_HOME=/android/sdk/avd
ENV ANDROID_EMULATOR_HOME=/android/sdk/emulator
ENV ANDROID_USER_HOME=/android/user_home/
ENV PATH=$ANDROID_HOME/cmdline-tools/latest/bin:$PATH
ENV PATH=$ANDROID_HOME/platform-tools:$PATH
ENV PATH=$ANDROID_HOME/emulator/:$PATH

# Installing latest version of the emulator
RUN yes | /android/sdk/cmdline-tools/latest/bin/sdkmanager --licenses
RUN /android/sdk/cmdline-tools/latest/bin/sdkmanager emulator

#RUN /android/sdk/cmdline-tools/latest/bin/sdkmanager "system-images;android-31;default;x86_64"
#RUN /android/sdk/cmdline-tools/latest/bin/avdmanager create avd -n test -k "system-images;android-31;default;x86_64"
#RUN /android/sdk/cmdline-tools/latest/bin/sdkmanager "system-images;android-31;google_apis;x86_64"
#RUN /android/sdk/cmdline-tools/latest/bin/avdmanager create avd -n test2 -k "system-images;android-31;google_apis;x86_64"

###################################
# Create start script
###################################
COPY ./emulator_build_service/emulator_start.sh /android/
RUN chmod +x /android/emulator_start.sh