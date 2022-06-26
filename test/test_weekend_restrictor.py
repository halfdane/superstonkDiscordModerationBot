from datetime import datetime, timezone

from posts.WeekendRestrictor import WeekendRestrictor
from freezegun import freeze_time
import pytest
import pytz


class TestWeekendRestrictor:
    nyse = pytz.timezone("America/New_York")

    @pytest.mark.parametrize(
        "a_timestamp, counts_as_weekend, description", [
            ('2022-06-01 08:15:27.243860', True, "wednesday"),
            ('2022-06-02 08:15:27.243860', True, "thursday"),
            ('2022-06-03 08:15:27.243860', True, "friday morning"),
            ('2022-06-03 15:59:27.243860', True, "friday shortly before close"),
            ('2022-06-03 16:00:00.000001', False, "friday shortly after close"),
            ('2022-06-04 08:15:27.243860', False, "saturday"),
            ('2022-06-05 08:15:27.243860', False, "sunday"),
            ('2022-06-06 08:15:27.243860', False, "monday morning"),
            ('2022-06-06 09:29:27.243860', False, "monday shortly before open"),
            ('2022-06-06 09:30:27.243860', True, "monday shortly after open"),
        ]
    )
    def test_weekend_calculation(self, a_timestamp, counts_as_weekend, description):
        testee = WeekendRestrictor(None)

        update_timestamp = datetime.strptime(a_timestamp, '%Y-%m-%d %H:%M:%S.%f')
        update_timestamp.replace(tzinfo=self.nyse)
        with freeze_time(update_timestamp):
            weekend = testee.it_is_not_weekend()
            assert weekend is counts_as_weekend
