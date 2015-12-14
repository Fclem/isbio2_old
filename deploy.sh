#!/bin/bash

SELF=`md5sum deploy.sh`
HOSTNAME=`hostname`

version=$(<.version)
((version++))
echo $version>.version

if [ "$HOSTNAME" = breeze.giu.fi ]; then
	echo "ON PROD ("$HOSTNAME")"
	ENVIRONMENT=production
	echo "git status"
	git status
	echo "git checkout"
	git checkout
	echo "git pull"
	git pull
else
	if [ "$HOSTNAME" = breeze-dev.giu.fi ]; then
		echo "ON DEV ("$HOSTNAME")"
		ENVIRONMENT=development
	fi
fi

NEW_SELF=`md5sum deploy.sh`
if [ $NEW_SELF != $SELF ]; then
	echo "Deploy script has been changed, re-starting..."
	./deploy.sh &
	exit $?
fi


ACCESS_TOKEN=00f2bf2c84ce40aa96842622c6ffe97d
LOCAL_USERNAME=`whoami`
REVISION=`git log -n 1 --pretty=format:"%H"`
echo "Registering deploy version "$version", git "$REVISION" ..."

curl https://api.rollbar.com/api/1/deploy/ \
  -F access_token=$ACCESS_TOKEN \
  -F environment=$ENVIRONMENT \
  -F revision=$REVISION \
  -F local_username=$LOCAL_USERNAME

echo ""
killall autorun.sh > /dev/null 2>&1
echo "Reloading BREEZE..."
./autorun.sh &
