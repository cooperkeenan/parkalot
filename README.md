# Parkalot automates the daily reservation process of booking a parking spot

## Timing

Spaces are released at 12:00 UK time. Each run waits until 12:00:06 UK time before booking, using the Europe/London time zone, so it adjusts automatically when the clocks change.

The Logic App must start the container before 12:00 UK time all year round. A start time of 10:50 UTC does this: it is 10:50 in winter and 11:50 in summer. If a run starts after booking opens, it tries straight away and logs a warning.

## Run logs

Each run saves its full log as one file in Azure Blob Storage, so the history survives after the container is deleted. Files go in the `parkalot-logs` container, named by start time and outcome:

```
2026/11/2026-11-09T11-59-30Z_OK.log
2026/11/2026-11-10T11-59-31Z_FAILED.log
```

The outcome is `FAILED` if anything was logged at ERROR level, `WARNING` if anything was logged at WARNING level, and `OK` otherwise.

### One-time setup

1. Create a storage account. The name must be globally unique, 3-24 lowercase letters and digits.

   ```bash
   az storage account create --name parkalotlogs<suffix> --resource-group parkalot-rg --sku Standard_LRS
   ```

2. Get its connection string.

   ```bash
   az storage account show-connection-string --name parkalotlogs<suffix> --resource-group parkalot-rg -o tsv
   ```

3. In the Logic App `parkalot-scheduler-v2`, add a **secure** environment variable `LOG_STORAGE_CONNECTION_STRING` with that value to the container the run creates.
4. Rebuild and push the image with `manager.sh`, option 1.

Optional: set `LOG_STORAGE_CONTAINER` to use a different blob container name.

If `LOG_STORAGE_CONNECTION_STRING` is not set, or the upload fails, the log is written to a local `logs/` folder instead. Logs are always printed to the console too.

### Reading the logs

List the most recent runs:

```bash
az storage blob list --connection-string "$LOG_STORAGE_CONNECTION_STRING" --container-name parkalot-logs --query "[].name" -o tsv | tail -20
```

Download one:

```bash
az storage blob download --connection-string "$LOG_STORAGE_CONNECTION_STRING" --container-name parkalot-logs --name <blob name> --file run.log
```

They can also be browsed in the Azure portal under the storage account's Containers page.
