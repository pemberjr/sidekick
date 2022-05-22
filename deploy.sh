# Used to deploy app via docker container
#

echo -e "Starting Docker deployment script...\n"

#check if container currently running

containerID=$(docker ps -a| grep sidekick-app | tr -s ' ' | cut -d ' ' -f 1)

echo -e "$containerID\n"
if [ -z "$containerID" ]
then
      echo "\$containerID is NULL"
else
      echo "\$containerID is NOT NULL"
      # Stop the currently running docker image
      docker stop sidekick-app
      # Remove all exited docker images
      docker rm sidekick-app
fi

# Rebuild and re-run docker images
docker build -t sidekick-app .
docker run -dp 5051:5051 --name sidekick-app --network airflow-tier -v /apps/sidekick:/sidekick sidekick-app

echo -e "\nFinished deploying docker container"
