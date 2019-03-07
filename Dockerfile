# https://github.com/CircleCI-Public/circleci-dockerfiles/blob/master/buildpack-deps/images/bionic/Dockerfile

FROM ubuntu:bionic

# make Apt non-interactive
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y git sudo openssh-client ca-certificates parallel net-tools gnupg curl wget pcregrep whois host language-pack-pl bridge-utils

CMD ["/bin/sh"]
