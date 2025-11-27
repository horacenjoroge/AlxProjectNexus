# Zero-Downtime Database Migration Strategy

**Last Updated:** 2025-11-22  
**Version:** 1.0.0

## Overview

This document outlines the strategy for deploying database migrations with zero downtime, ensuring backward compatibility and providing rollback capabilities.

## Principles

1. **Backward Compatibility**: All migrations must be backward-compatible with the previous code version
2. **Zero Downtime**: Application remains available during migration
3. **Safety First**: Always backup before migration
4. **Rollback Ready**: Every migration must have a rollback plan
5. **Validation**: Test migrations in staging before production

## Migration Types

### 1. Safe Migrations (No Downtime Required)

These migrations can be applied without downtime:

- **Adding new columns** (with default values or nullable)
- **Adding new tables**
- **Adding indexes** (concurrent in PostgreSQL)
- **Adding constraints** (if not immediately enforced)
- **Data migrations** (read-only or additive)

**Example:**
```python
# Safe: Adding nullable column
migrations.AddField(
    model_name='poll',
    name='new_field',
    field=models.CharField(max_length=100, null=True, blank=True),
)
```

### 2. Potentially Risky Migrations (Require Careful Planning)

These migrations need special handling:

- **Removing columns** (requires code deployment first)
- **Changing column types** (requires data migration)
- **Adding NOT NULL constraints** (requires default values)
- **Removing tables** (requires code deployment first)

**Example:**
```python
# Risky: Removing column - must deploy code first, then migrate
# Step 1: Deploy code that doesn't use the column
# Step 2: Run migration to remove column
migrations.RemoveField(
    model_name='poll',
    name='old_field',
)
```

### 3. Dangerous Migrations (Require Maintenance Window)

These migrations may require brief downtime:

- **Renaming columns** (requires both code and migration)
- **Changing primary keys**
- **Major schema restructuring**

**Example:**
```python
# Dangerous: Renaming column - requires coordinated deployment
# Step 1: Add new column
# Step 2: Deploy code that uses new column
# Step 3: Migrate data
# Step 4: Remove old column
```

## Migration Workflow

### Phase 1: Pre-Migration (Preparation)

1. **Review Migration**
   ```bash
   # Check migration for backward compatibility
   python manage.py check_migration_safety <app_name> <migration_name>
   ```

2. **Create Backup**
   ```bash
   # Automated backup before migration
   ./scripts/backup-database.sh --pre-migration
   ```

3. **Test in Staging**
   ```bash
   # Apply migration in staging
   python manage.py migrate --settings=config.settings.staging
   
   # Verify application works
   # Run smoke tests
   ```

### Phase 2: Migration Execution

1. **Validate Migration**
   ```bash
   # Check migration can be applied
   python manage.py validate_migration <app_name> <migration_name>
   ```

2. **Apply Migration**
   ```bash
   # For safe migrations (zero downtime)
   python manage.py migrate --no-downtime
   
   # For risky migrations (with monitoring)
   python manage.py migrate --monitor --rollback-on-error
   ```

3. **Verify Migration**
   ```bash
   # Check migration was applied
   python manage.py showmigrations
   
   # Verify application health
   curl http://localhost/health/
   ```

### Phase 3: Post-Migration (Verification)

1. **Health Checks**
   ```bash
   # Verify all services healthy
   docker-compose -f docker/docker-compose.prod.yml ps
   
   # Check application endpoints
   curl http://localhost/api/v1/
   ```

2. **Data Verification**
   ```bash
   # Verify data integrity
   python manage.py verify_migration_data <app_name> <migration_name>
   ```

3. **Performance Check**
   ```bash
   # Monitor query performance
   # Check slow query logs
   ```

## Blue-Green Deployment Strategy

### Overview

Blue-Green deployment maintains two identical production environments:
- **Blue**: Current production (serving traffic)
- **Green**: New version (with migrations applied)

### Workflow

1. **Prepare Green Environment**
   ```bash
   # Start green environment
   docker-compose -f docker/docker-compose.prod-green.yml up -d
   
   # Apply migrations to green
   docker-compose -f docker/docker-compose.prod-green.yml exec web \
     python manage.py migrate --settings=config.settings.production
   ```

2. **Verify Green Environment**
   ```bash
   # Health checks
   curl http://green.yourdomain.com/health/
   
   # Smoke tests
   pytest backend/tests/test_smoke.py
   ```

3. **Switch Traffic**
   ```bash
   # Update load balancer to point to green
   # Or update Nginx upstream configuration
   ```

4. **Monitor**
   ```bash
   # Monitor green environment
   # Check logs, metrics, errors
   ```

5. **Rollback (if needed)**
   ```bash
   # Switch traffic back to blue
   # Investigate issues in green
   ```

6. **Cleanup**
   ```bash
   # After successful deployment, blue becomes new green
   # Update blue with latest code for next deployment
   ```

## Rollback Procedures

### Automatic Rollback

The migration system can automatically rollback on errors:

```bash
# Enable automatic rollback
python manage.py migrate --rollback-on-error --backup-before
```

### Manual Rollback

1. **Identify Migration to Rollback**
   ```bash
   # List applied migrations
   python manage.py showmigrations
   ```

2. **Restore Backup**
   ```bash
   # Restore database from backup
   ./scripts/restore-database.sh backup_YYYYMMDD_HHMMSS.sql.gz
   ```

3. **Rollback Migration**
   ```bash
   # Rollback specific migration
   python manage.py migrate <app_name> <previous_migration>
   ```

4. **Verify Rollback**
   ```bash
   # Check application works
   curl http://localhost/health/
   
   # Verify data integrity
   python manage.py verify_migration_data
   ```

## Best Practices

### 1. Migration Design

- **Always add columns as nullable first**, then populate, then make required
- **Use data migrations** for complex data transformations
- **Test migrations** on production-like data volumes
- **Document breaking changes** in migration comments

### 2. Deployment Timing

- **Deploy during low-traffic periods** when possible
- **Monitor during deployment** for any issues
- **Have rollback plan ready** before starting
- **Communicate with team** about deployment window

### 3. Code Deployment

- **Deploy code before removing columns/tables**
- **Deploy code after adding required columns**
- **Use feature flags** for gradual rollouts
- **Monitor error rates** after deployment

### 4. Testing

- **Test migrations in staging** with production-like data
- **Run migration dry-run** before production
- **Test rollback procedures** regularly
- **Load test** after migration

## Migration Checklist

### Before Migration

- [ ] Migration reviewed for backward compatibility
- [ ] Backup created and verified
- [ ] Migration tested in staging
- [ ] Rollback plan documented
- [ ] Team notified of deployment window
- [ ] Monitoring dashboards ready

### During Migration

- [ ] Migration applied successfully
- [ ] Health checks passing
- [ ] Application responding correctly
- [ ] No error rate increase
- [ ] Performance metrics normal

### After Migration

- [ ] All services healthy
- [ ] Data integrity verified
- [ ] Performance acceptable
- [ ] Monitoring shows no issues
- [ ] Backup of post-migration state created

## Tools and Scripts

### Management Commands

- `python manage.py check_migration_safety` - Check migration safety
- `python manage.py validate_migration` - Validate migration can be applied
- `python manage.py migrate --no-downtime` - Apply safe migrations
- `python manage.py rollback_migration` - Rollback specific migration
- `python manage.py verify_migration_data` - Verify data after migration

### Shell Scripts

- `scripts/backup-database.sh` - Create database backup
- `scripts/restore-database.sh` - Restore from backup
- `scripts/migrate-safe.sh` - Safe migration wrapper
- `scripts/blue-green-deploy.sh` - Blue-green deployment script

## Emergency Procedures

### Migration Fails Mid-Execution

1. **Stop migration** (if possible)
2. **Check database state** - `python manage.py showmigrations`
3. **Restore from backup** if database corrupted
4. **Investigate cause** - Check logs, migration file
5. **Fix migration** and retry in staging
6. **Document issue** for future reference

### Application Errors After Migration

1. **Check error logs** - `docker-compose logs web`
2. **Verify migration applied correctly** - `python manage.py showmigrations`
3. **Check data integrity** - `python manage.py verify_migration_data`
4. **Rollback if necessary** - Use rollback procedures
5. **Investigate root cause** before retrying

### Performance Degradation

1. **Check slow queries** - PostgreSQL slow query log
2. **Verify indexes** - `\di` in PostgreSQL
3. **Analyze query plans** - `EXPLAIN ANALYZE`
4. **Add missing indexes** if needed
5. **Consider rollback** if critical

## Monitoring

### Key Metrics

- **Migration duration** - Time to apply migration
- **Application availability** - Uptime during migration
- **Error rate** - Should remain stable
- **Query performance** - Response times
- **Database locks** - Should be minimal

### Alerts

- Migration takes longer than expected
- Application health checks fail
- Error rate increases
- Database locks detected
- Performance degradation

## Examples

### Example 1: Adding a New Column (Safe)

```python
# Migration: 0007_add_poll_category.py
class Migration(migrations.Migration):
    dependencies = [
        ('polls', '0006_category_poll_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='poll',
            name='priority',
            field=models.IntegerField(default=0, null=True, blank=True),
        ),
    ]
```

**Deployment:**
```bash
# 1. Backup
./scripts/backup-database.sh --pre-migration

# 2. Apply migration (zero downtime)
python manage.py migrate polls 0007_add_poll_category

# 3. Deploy code that uses new column
# (Code can work with or without the column)

# 4. Verify
python manage.py verify_migration_data polls 0007_add_poll_category
```

### Example 2: Removing a Column (Risky)

```python
# Migration: 0008_remove_old_field.py
class Migration(migrations.Migration):
    dependencies = [
        ('polls', '0007_add_poll_category'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='poll',
            name='old_field',
        ),
    ]
```

**Deployment:**
```bash
# 1. Deploy code that doesn't use old_field
# (Code must not reference old_field)

# 2. Backup
./scripts/backup-database.sh --pre-migration

# 3. Apply migration
python manage.py migrate polls 0008_remove_old_field

# 4. Verify
python manage.py verify_migration_data polls 0008_remove_old_field
```

### Example 3: Data Migration (Safe)

```python
# Migration: 0009_populate_priority.py
def populate_priority(apps, schema_editor):
    Poll = apps.get_model('polls', 'Poll')
    for poll in Poll.objects.all():
        poll.priority = calculate_priority(poll)
        poll.save()

class Migration(migrations.Migration):
    dependencies = [
        ('polls', '0008_remove_old_field'),
    ]

    operations = [
        migrations.RunPython(populate_priority, migrations.RunPython.noop),
    ]
```

**Deployment:**
```bash
# 1. Backup
./scripts/backup-database.sh --pre-migration

# 2. Apply migration (runs data migration)
python manage.py migrate polls 0009_populate_priority

# 3. Verify data
python manage.py verify_migration_data polls 0009_populate_priority
```

## References

- [Django Migrations Documentation](https://docs.djangoproject.com/en/stable/topics/migrations/)
- [PostgreSQL Concurrent Indexes](https://www.postgresql.org/docs/current/sql-createindex.html#SQL-CREATEINDEX-CONCURRENTLY)
- [Blue-Green Deployment](https://martinfowler.com/bliki/BlueGreenDeployment.html)


