# Generated migration for API Key security enhancements

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api_keys", "0003_alter_apikey_name_alter_apikey_scope"),
    ]

    operations = [
        # Add new fields to APIKey model
        migrations.AddField(
            model_name="apikey",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="apikey",
            name="last_used_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="apikey",
            name="expires_at",
            field=models.DateTimeField(
                blank=True, null=True, help_text="Optional expiration date"
            ),
        ),
        migrations.AddField(
            model_name="apikey",
            name="allowed_ips",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text="List of allowed IP addresses. Empty = allow all",
            ),
        ),
        migrations.AddField(
            model_name="apikey",
            name="rate_limit_per_minute",
            field=models.PositiveIntegerField(
                blank=True,
                null=True,
                help_text="Custom rate limit for this key (overrides default)",
            ),
        ),
        migrations.AddField(
            model_name="apikey",
            name="metadata",
            field=models.JSONField(
                blank=True, default=dict, help_text="Custom metadata"
            ),
        ),
        migrations.AddField(
            model_name="apikey",
            name="revoked_reason",
            field=models.TextField(blank=True, help_text="Reason for revocation"),
        ),
        
        # Update Status choices to include EXPIRED
        migrations.AlterField(
            model_name="apikey",
            name="status",
            field=models.CharField(
                choices=[
                    ("active", "Active"),
                    ("revoked", "Revoked"),
                    ("expired", "Expired"),
                ],
                default="active",
                max_length=20,
            ),
        ),
        
        # Update organization relationship to include related_name
        migrations.AlterField(
            model_name="apikey",
            name="organization",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="api_keys",
                to="organizations.organization",
            ),
        ),
        
        # Update quota field help text
        migrations.AlterField(
            model_name="apikey",
            name="quota",
            field=models.PositiveIntegerField(
                blank=True, null=True, help_text="Max requests allowed"
            ),
        ),
        
        # Create APIKeyUsageLog model
        migrations.CreateModel(
            name="APIKeyUsageLog",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("timestamp", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("endpoint", models.CharField(max_length=255)),
                ("method", models.CharField(max_length=10)),
                ("ip_address", models.GenericIPAddressField()),
                ("user_agent", models.TextField(blank=True)),
                ("status_code", models.PositiveSmallIntegerField()),
                (
                    "response_time_ms",
                    models.PositiveIntegerField(
                        help_text="Response time in milliseconds"
                    ),
                ),
                (
                    "tokens_used",
                    models.PositiveIntegerField(
                        default=0, help_text="LLM tokens consumed"
                    ),
                ),
                ("documents_searched", models.PositiveSmallIntegerField(default=0)),
                ("error_message", models.TextField(blank=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                (
                    "api_key",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="usage_logs",
                        to="api_keys.apikey",
                    ),
                ),
            ],
            options={
                "verbose_name": "API Key Usage Log",
                "verbose_name_plural": "API Key Usage Logs",
                "ordering": ["-timestamp"],
            },
        ),
        
        # Add indexes to APIKey model
        migrations.AddIndex(
            model_name="apikey",
            index=models.Index(
                fields=["organization", "-created_at"],
                name="api_keys_or_org_created_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="apikey",
            index=models.Index(
                fields=["status", "-last_used_at"],
                name="api_keys_status_last_used_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="apikey",
            index=models.Index(
                fields=["expires_at"],
                name="api_keys_expires_at_idx",
            ),
        ),
        
        # Add indexes to APIKeyUsageLog model
        migrations.AddIndex(
            model_name="apikeyusagelog",
            index=models.Index(
                fields=["api_key", "-timestamp"],
                name="api_key_usage_key_ts_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="apikeyusagelog",
            index=models.Index(
                fields=["endpoint", "-timestamp"],
                name="api_key_usage_endpoint_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="apikeyusagelog",
            index=models.Index(
                fields=["ip_address", "-timestamp"],
                name="api_key_usage_ip_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="apikeyusagelog",
            index=models.Index(
                fields=["-timestamp"],
                name="api_key_usage_ts_idx",
            ),
        ),
        
        # Add Meta options to APIKey
        migrations.AlterModelOptions(
            name="apikey",
            options={
                "ordering": ["-created_at"],
                "verbose_name": "API Key",
                "verbose_name_plural": "API Keys",
            },
        ),
    ]
