# Configuration for Call Center Panel

# CUSTOMER RE-CALL WAITING PERIOD
# How many days to wait before showing the same customer to operator again
# Default: 7 days (1 week)
RECALL_WAITING_DAYS = 7

# Examples:
# RECALL_WAITING_DAYS = 1   # 1 day (24 hours)
# RECALL_WAITING_DAYS = 3   # 3 days
# RECALL_WAITING_DAYS = 7   # 1 week (default)
# RECALL_WAITING_DAYS = 14  # 2 weeks
# RECALL_WAITING_DAYS = 30  # 1 month

# STALE ASSIGNMENT TIMEOUT
# How many minutes before releasing stuck assignments
STALE_ASSIGNMENT_MINUTES = 10

# MAXIMUM CALL ATTEMPTS
# How many times to try calling a customer before cooldown
MAX_CALL_ATTEMPTS = 3

# COOLDOWN PERIOD AFTER MAX ATTEMPTS
# How many days to wait after MAX_CALL_ATTEMPTS before resetting and re-adding to pool
# After this period, call_attempts resets to 0 and customer becomes available again
COOLDOWN_DAYS = 14
