from app.services.quota import load_quota_config


def test_load_quota_config_reads_values(tmp_path):
    config_path = tmp_path / "quota.yaml"
    config_path.write_text(
        """
        {
          "quota": {
            "dailyLimit": 120,
            "concurrencyLimit": 4,
            "resetPolicy": {
              "timeZone": "UTC",
              "resetHour": 2
            }
          }
        }
        """
    )

    config = load_quota_config(path=config_path)

    assert config.daily_limit == 120
    assert config.concurrency_limit == 4
    assert config.reset_policy.time_zone == "UTC"
    assert config.reset_policy.reset_hour == 2
