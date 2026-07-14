#!/bin/bash
set -e

echo "Executing docker-entrypoint.sh..."

# Check if the necessary setup has been done
if [ ! -f "$HOME/.initialized" ]; then

  echo "Initializing the application..."

  # Check if local_settings.py file exists
#   if [ ! -f ./assetmanagemen/local_settings.py ]; then
#     echo "Copying local_settings_sample.py to local_settings.py..."
#     cp ./assetmanagemen/local_settings_sample.py ./assetmanagemen/local_settings.py
#   fi

  if [ "$DEPLOYMENT" == "production" ]; then
    #Copy the static files to the static root
    echo "Copying static files to static root..."
    python manage.py collectstatic --noinput
  fi

  # Run the migration and other initialization tasks
  echo "Running migrations..."
  python manage.py migrate

  # Run other management commands or setup tasks as needed
  echo "Creating permission groups..."
  # Only run if command exists or is properly configured
  python manage.py create_permission_groups || echo "Skipping create_permission_groups"

  # Create a superuser
  echo "Creating superuser..."
  # Note: --noinput requires DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL, and DJANGO_SUPERUSER_PASSWORD environment variables
  python manage.py createsuperuser --noinput || echo "Superuser creation skipped or failed. Ensure env vars are set if needed."

  # Create a flag file to indicate initialization is done
  touch "$HOME/.initialized"
fi

# Pass the container command arguments to the command
exec "$@"
