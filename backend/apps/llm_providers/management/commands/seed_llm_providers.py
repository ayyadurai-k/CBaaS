from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.llm_providers.models import LLMProvider, LLMModel


class Command(BaseCommand):
    help = 'Seed the database with default LLM providers and models'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reseed even if providers already exist',
        )
        parser.add_argument(
            '--update-existing',
            action='store_true',
            help='Update existing providers and models with new data',
        )

    def handle(self, *args, **options):
        force = options['force']
        update_existing = options['update_existing']

        # Check if providers already exist
        if LLMProvider.objects.exists() and not force and not update_existing:
            self.stdout.write(
                self.style.WARNING(
                    'LLM providers already exist. Use --force to recreate or --update-existing to update them.'
                )
            )
            return

        # Default provider and model configurations
        providers_data = {
            'openai': {
                'display_name': 'OpenAI',
                'description': 'OpenAI GPT models for chat and completion',
                'api_base_url': 'https://api.openai.com/v1',
                'models': [
                    {
                        'name': 'gpt-3.5-turbo',
                        'display_name': 'GPT-3.5 Turbo',
                        'description': 'Fast and efficient model for most conversations',
                        'context_window': 16384,
                        'max_tokens': 4096,
                        'supports_streaming': True,
                        'supports_function_calling': True,
                        'cost_per_1k_input_tokens': 0.0005,
                        'cost_per_1k_output_tokens': 0.0015,
                        'is_default': True
                    },
                    {
                        'name': 'gpt-4',
                        'display_name': 'GPT-4',
                        'description': 'Most capable model for complex tasks',
                        'context_window': 8192,
                        'max_tokens': 8192,
                        'supports_streaming': True,
                        'supports_function_calling': True,
                        'cost_per_1k_input_tokens': 0.03,
                        'cost_per_1k_output_tokens': 0.06,
                        'is_default': False
                    },
                    {
                        'name': 'gpt-4o',
                        'display_name': 'GPT-4o',
                        'description': 'Latest GPT-4 Omni model with multimodal capabilities',
                        'context_window': 128000,
                        'max_tokens': 4096,
                        'supports_streaming': True,
                        'supports_function_calling': True,
                        'cost_per_1k_input_tokens': 0.005,
                        'cost_per_1k_output_tokens': 0.015,
                        'is_default': False
                    }
                ]
            },
            'gemini': {
                'display_name': 'Google Gemini',
                'description': 'Google\'s advanced AI model family',
                'api_base_url': 'https://generativelanguage.googleapis.com/v1beta',
                'models': [
                    {
                        'name': 'gemini-pro',
                        'display_name': 'Gemini Pro',
                        'description': 'Google\'s most capable model for text tasks',
                        'context_window': 32768,
                        'max_tokens': 8192,
                        'supports_streaming': True,
                        'supports_function_calling': True,
                        'cost_per_1k_input_tokens': 0.000125,
                        'cost_per_1k_output_tokens': 0.000375,
                        'is_default': True
                    },
                    {
                        'name': 'gemini-1.5-pro',
                        'display_name': 'Gemini 1.5 Pro',
                        'description': 'Advanced Gemini model with larger context window',
                        'context_window': 2000000,
                        'max_tokens': 8192,
                        'supports_streaming': True,
                        'supports_function_calling': True,
                        'cost_per_1k_input_tokens': 0.00125,
                        'cost_per_1k_output_tokens': 0.00375,
                        'is_default': False
                    }
                ]
            },
            'deepseek': {
                'display_name': 'DeepSeek',
                'description': 'DeepSeek AI models specialized for reasoning and coding',
                'api_base_url': 'https://api.deepseek.com/v1',
                'models': [
                    {
                        'name': 'deepseek-chat',
                        'display_name': 'DeepSeek Chat',
                        'description': 'General purpose conversational AI model',
                        'context_window': 32768,
                        'max_tokens': 4096,
                        'supports_streaming': True,
                        'supports_function_calling': False,
                        'cost_per_1k_input_tokens': 0.00014,
                        'cost_per_1k_output_tokens': 0.00028,
                        'is_default': True
                    },
                    {
                        'name': 'deepseek-coder',
                        'display_name': 'DeepSeek Coder',
                        'description': 'Specialized model for code generation and programming tasks',
                        'context_window': 16384,
                        'max_tokens': 4096,
                        'supports_streaming': True,
                        'supports_function_calling': False,
                        'cost_per_1k_input_tokens': 0.00014,
                        'cost_per_1k_output_tokens': 0.00028,
                        'is_default': False
                    }
                ]
            }
        }

        try:
            with transaction.atomic():
                if force:
                    # Delete existing data
                    self.stdout.write('Deleting existing providers and models...')
                    LLMModel.objects.all().delete()
                    LLMProvider.objects.all().delete()

                # Create or update providers and models
                for provider_key, provider_data in providers_data.items():
                    models_data = provider_data.pop('models')
                    
                    provider, created = LLMProvider.objects.update_or_create(
                        name=provider_key,
                        defaults=provider_data
                    )
                    
                    if created:
                        self.stdout.write(
                            self.style.SUCCESS(f'✓ Created provider: {provider.display_name}')
                        )
                    elif update_existing:
                        self.stdout.write(
                            self.style.WARNING(f'⟳ Updated provider: {provider.display_name}')
                        )

                    # Clear existing default models for this provider to avoid conflicts
                    if update_existing or force:
                        LLMModel.objects.filter(provider=provider, is_default=True).update(is_default=False)

                    # Create or update models
                    for model_data in models_data:
                        model, created = LLMModel.objects.update_or_create(
                            provider=provider,
                            name=model_data['name'],
                            defaults=model_data
                        )
                        
                        if created:
                            self.stdout.write(
                                self.style.SUCCESS(f'  ✓ Created model: {model.display_name}')
                            )
                        elif update_existing:
                            self.stdout.write(
                                self.style.WARNING(f'  ⟳ Updated model: {model.display_name}')
                            )

                # Summary
                provider_count = LLMProvider.objects.count()
                model_count = LLMModel.objects.count()
                active_provider_count = LLMProvider.objects.filter(is_active=True).count()
                active_model_count = LLMModel.objects.filter(is_active=True).count()

                self.stdout.write('\n' + '='*50)
                self.stdout.write(self.style.SUCCESS('Database seeding completed successfully!'))
                self.stdout.write(f'Total providers: {provider_count} (active: {active_provider_count})')
                self.stdout.write(f'Total models: {model_count} (active: {active_model_count})')
                self.stdout.write('='*50)

        except Exception as e:
            raise CommandError(f'Error seeding database: {str(e)}')