"""
Datetime Tools Plugin

Provides date, time, and datetime manipulation tools.
"""

import datetime
import time
import pytz
from typing import Dict, Any, List, Optional, Union
from dateutil import parser as dateutil_parser
from dateutil.relativedelta import relativedelta


def get_current_time(timezone: str = None) -> Dict[str, Any]:
    """Get the current date and time."""
    now = datetime.datetime.now()
    
    if timezone:
        try:
            tz = pytz.timezone(timezone)
            now = datetime.datetime.now(tz)
        except Exception:
            pass
    
    return {
        "datetime": now.isoformat(),
        "date": now.date().isoformat(),
        "time": now.time().isoformat(),
        "timestamp": now.timestamp(),
        "year": now.year,
        "month": now.month,
        "day": now.day,
        "hour": now.hour,
        "minute": now.minute,
        "second": now.second,
        "weekday": now.weekday(),
        "weekday_name": now.strftime("%A"),
        "month_name": now.strftime("%B"),
        "timezone": str(now.tzinfo) if now.tzinfo else "local",
        "formatted": now.strftime("%Y-%m-%d %H:%M:%S"),
        "success": True,
    }


def get_current_date(timezone: str = None) -> Dict[str, Any]:
    """Get the current date."""
    result = get_current_time(timezone)
    return {
        "date": result["date"],
        "year": result["year"],
        "month": result["month"],
        "day": result["day"],
        "weekday": result["weekday"],
        "weekday_name": result["weekday_name"],
        "month_name": result["month_name"],
        "formatted": result["date"],
        "success": True,
    }


def get_current_time_only(timezone: str = None) -> Dict[str, Any]:
    """Get the current time only."""
    result = get_current_time(timezone)
    return {
        "time": result["time"],
        "hour": result["hour"],
        "minute": result["minute"],
        "second": result["second"],
        "formatted": result["time"],
        "success": True,
    }


def parse_datetime(datetime_str: str, formats: List[str] = None) -> Dict[str, Any]:
    """Parse a datetime string into a datetime object."""
    try:
        if formats:
            for fmt in formats:
                try:
                    dt = datetime.datetime.strptime(datetime_str, fmt)
                    return {
                        "datetime": dt.isoformat(),
                        "parsed_from": fmt,
                        "year": dt.year,
                        "month": dt.month,
                        "day": dt.day,
                        "hour": dt.hour,
                        "minute": dt.minute,
                        "second": dt.second,
                        "success": True,
                    }
                except ValueError:
                    continue
        
        dt = dateutil_parser.parse(datetime_str)
        return {
            "datetime": dt.isoformat(),
            "parsed_from": "auto",
            "year": dt.year,
            "month": dt.month,
            "day": dt.day,
            "hour": dt.hour if hasattr(dt, 'hour') else 0,
            "minute": dt.minute if hasattr(dt, 'minute') else 0,
            "second": dt.second if hasattr(dt, 'second') else 0,
            "success": True,
        }
    except Exception as e:
        return {"error": str(e), "datetime_str": datetime_str, "success": False}


def format_datetime(datetime_obj: Union[str, datetime.datetime], format_str: str = None) -> Dict[str, Any]:
    """Format a datetime object as a string."""
    try:
        if isinstance(datetime_obj, str):
            dt = dateutil_parser.parse(datetime_obj)
        else:
            dt = datetime_obj
        
        if format_str:
            result = dt.strftime(format_str)
        else:
            result = dt.isoformat()
        
        return {"formatted": result, "datetime": dt.isoformat(), "format": format_str, "success": True}
    except Exception as e:
        return {"error": str(e), "success": False}


def add_time(datetime_str: str, delta: Dict[str, Any]) -> Dict[str, Any]:
    """Add time to a datetime."""
    try:
        dt = dateutil_parser.parse(datetime_str)
        
        delta_kwargs = {}
        if "years" in delta:
            delta_kwargs["years"] = delta["years"]
        if "months" in delta:
            delta_kwargs["months"] = delta["months"]
        if "weeks" in delta:
            delta_kwargs["weeks"] = delta["weeks"]
        if "days" in delta:
            delta_kwargs["days"] = delta["days"]
        if "hours" in delta:
            delta_kwargs["hours"] = delta["hours"]
        if "minutes" in delta:
            delta_kwargs["minutes"] = delta["minutes"]
        if "seconds" in delta:
            delta_kwargs["seconds"] = delta["seconds"]
        
        new_dt = dt + relativedelta(**delta_kwargs)
        
        return {
            "original": dt.isoformat(),
            "new": new_dt.isoformat(),
            "delta": delta,
            "success": True,
        }
    except Exception as e:
        return {"error": str(e), "datetime_str": datetime_str, "delta": delta, "success": False}


def subtract_time(datetime_str: str, delta: Dict[str, Any]) -> Dict[str, Any]:
    """Subtract time from a datetime."""
    try:
        dt = dateutil_parser.parse(datetime_str)
        
        delta_kwargs = {}
        if "years" in delta:
            delta_kwargs["years"] = -delta["years"]
        if "months" in delta:
            delta_kwargs["months"] = -delta["months"]
        if "weeks" in delta:
            delta_kwargs["weeks"] = -delta["weeks"]
        if "days" in delta:
            delta_kwargs["days"] = -delta["days"]
        if "hours" in delta:
            delta_kwargs["hours"] = -delta["hours"]
        if "minutes" in delta:
            delta_kwargs["minutes"] = -delta["minutes"]
        if "seconds" in delta:
            delta_kwargs["seconds"] = -delta["seconds"]
        
        new_dt = dt + relativedelta(**delta_kwargs)
        
        return {
            "original": dt.isoformat(),
            "new": new_dt.isoformat(),
            "delta": delta,
            "success": True,
        }
    except Exception as e:
        return {"error": str(e), "datetime_str": datetime_str, "delta": delta, "success": False}


def time_between(datetime1: str, datetime2: str) -> Dict[str, Any]:
    """Calculate the time difference between two datetimes."""
    try:
        dt1 = dateutil_parser.parse(datetime1)
        dt2 = dateutil_parser.parse(datetime2)
        
        if dt2 < dt1:
            dt1, dt2 = dt2, dt1
        
        delta = dt2 - dt1
        
        total_seconds = delta.total_seconds()
        total_minutes = total_seconds / 60
        total_hours = total_minutes / 60
        total_days = total_hours / 24
        total_weeks = total_days / 7
        total_months = total_days / 30.44
        total_years = total_days / 365.25
        
        return {
            "datetime1": dt1.isoformat(),
            "datetime2": dt2.isoformat(),
            "difference": {
                "days": delta.days,
                "seconds": delta.seconds,
                "microseconds": delta.microseconds,
                "total_seconds": total_seconds,
                "total_minutes": total_minutes,
                "total_hours": total_hours,
                "total_days": total_days,
                "total_weeks": total_weeks,
                "total_months": total_months,
                "total_years": total_years,
            },
            "formatted": f"{delta.days} days, {delta.seconds // 3600} hours, {(delta.seconds % 3600) // 60} minutes, {delta.seconds % 60} seconds",
            "success": True,
        }
    except Exception as e:
        return {"error": str(e), "datetime1": datetime1, "datetime2": datetime2, "success": False}


def is_leap_year(year: int) -> Dict[str, Any]:
    """Check if a year is a leap year."""
    try:
        is_leap = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
        return {
            "year": year,
            "is_leap": is_leap,
            "days_in_february": 29 if is_leap else 28,
            "success": True,
        }
    except Exception as e:
        return {"error": str(e), "year": year, "success": False}


def get_timezone_list() -> Dict[str, Any]:
    """Get a list of all available timezones."""
    try:
        timezones = list(pytz.all_timezones)
        return {
            "timezones": timezones,
            "count": len(timezones),
            "success": True,
        }
    except Exception as e:
        return {"error": str(e), "success": False}


def convert_timezone(datetime_str: str, from_tz: str, to_tz: str) -> Dict[str, Any]:
    """Convert a datetime from one timezone to another."""
    try:
        dt = dateutil_parser.parse(datetime_str)
        
        if dt.tzinfo is None:
            from_zone = pytz.timezone(from_tz)
            dt = from_zone.localize(dt)
        else:
            from_zone = pytz.timezone(from_tz)
            dt = dt.astimezone(from_zone)
        
        to_zone = pytz.timezone(to_tz)
        converted = dt.astimezone(to_zone)
        
        return {
            "original": dt.isoformat(),
            "from_timezone": from_tz,
            "to_timezone": to_tz,
            "converted": converted.isoformat(),
            "success": True,
        }
    except Exception as e:
        return {"error": str(e), "datetime_str": datetime_str, "from_tz": from_tz, "to_tz": to_tz, "success": False}


def get_unix_timestamp(datetime_str: str = None) -> Dict[str, Any]:
    """Get Unix timestamp (seconds since epoch)."""
    try:
        if datetime_str:
            dt = dateutil_parser.parse(datetime_str)
        else:
            dt = datetime.datetime.now()
        
        timestamp = dt.timestamp()
        
        return {
            "datetime": dt.isoformat(),
            "timestamp": timestamp,
            "timestamp_ms": timestamp * 1000,
            "success": True,
        }
    except Exception as e:
        return {"error": str(e), "success": False}


def timestamp_to_datetime(timestamp: float) -> Dict[str, Any]:
    """Convert Unix timestamp to datetime."""
    try:
        dt = datetime.datetime.fromtimestamp(timestamp)
        return {
            "timestamp": timestamp,
            "datetime": dt.isoformat(),
            "year": dt.year,
            "month": dt.month,
            "day": dt.day,
            "hour": dt.hour,
            "minute": dt.minute,
            "second": dt.second,
            "success": True,
        }
    except Exception as e:
        return {"error": str(e), "timestamp": timestamp, "success": False}


PLUGIN_METADATA = {
    "name": "datetime_tools",
    "version": "1.0.0",
    "description": "Date, time, and datetime manipulation tools",
    "author": "Self System",
    "functions": [
        {"name": "get_current_time", "description": "Get current date and time"},
        {"name": "get_current_date", "description": "Get current date"},
        {"name": "get_current_time_only", "description": "Get current time only"},
        {"name": "parse_datetime", "description": "Parse datetime string"},
        {"name": "format_datetime", "description": "Format datetime as string"},
        {"name": "add_time", "description": "Add time to datetime"},
        {"name": "subtract_time", "description": "Subtract time from datetime"},
        {"name": "time_between", "description": "Calculate time difference between two datetimes"},
        {"name": "is_leap_year", "description": "Check if year is leap year"},
        {"name": "get_timezone_list", "description": "Get list of all timezones"},
        {"name": "convert_timezone", "description": "Convert datetime between timezones"},
        {"name": "get_unix_timestamp", "description": "Get Unix timestamp"},
        {"name": "timestamp_to_datetime", "description": "Convert Unix timestamp to datetime"},
    ],
}


def get_metadata() -> Dict[str, Any]:
    """Return plugin metadata."""
    return PLUGIN_METADATA
