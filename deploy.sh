
# Used to deploy app via docker container
#

echo -e "Starting Docker deployment script...\n"

#check if container currently running

containerID=$(docker ps | grep netmri-discovery-app | tr -s ' ' | cut -d ' ' -f 1)

echo -e "$containerID\n"
if [ -z "$containerID" ]
then
      echo "\$containerID is NULL"
else
      echo "\$containerID is NOT NULL"
      # Stop the currently running docker image
      docker stop netmri-discovery-app
      # Remove all exited docker images
      docker rm netmri-discovery-app
fi

# Rebuild and re-run docker images
docker build -t netmri-discovery-app .
docker run -dp 5050:5050 --name netmri-discovery-app -v /apps/NETMRI_Discovery:/NETMRI_Discovery netmri-discovery-app

echo -e "\nFinished deploying docker container"