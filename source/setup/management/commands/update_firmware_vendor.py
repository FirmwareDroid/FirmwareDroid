# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
from django.core.management.base import BaseCommand, CommandError
from firmware_handler.firmware_os_detect import update_firmware_vendor_by_build_prop
from model import AndroidFirmware


class Command(BaseCommand):
    help = 'Update OS vendor information for firmware based on build.prop files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--firmware-ids',
            nargs='+',
            type=str,
            help='Specific firmware IDs to update (if not provided, updates all firmware with Unknown vendor)',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Update all firmware regardless of current vendor value',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making actual changes',
        )

    def handle(self, *args, **options):
        firmware_ids = options.get('firmware_ids')
        update_all = options.get('all', False)
        dry_run = options.get('dry_run', False)

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        try:
            # Determine which firmware to process
            if firmware_ids:
                # Process specific firmware IDs
                firmware_list = AndroidFirmware.objects(id__in=firmware_ids)
                self.stdout.write(f'Processing {len(firmware_list)} specific firmware records...')
            elif update_all:
                # Process all firmware
                firmware_list = AndroidFirmware.objects()
                self.stdout.write(f'Processing all {len(firmware_list)} firmware records...')
            else:
                # Process only firmware with 'Unknown' vendor (default behavior)
                firmware_list = AndroidFirmware.objects(os_vendor='Unknown')
                self.stdout.write(f'Processing {len(firmware_list)} firmware records with Unknown vendor...')

            if dry_run:
                # Simulate updates without actual changes
                updated_count = 0
                for firmware in firmware_list:
                    if firmware.build_prop_file_id_list:
                        from firmware_handler.firmware_os_detect import detect_vendor_by_build_prop
                        build_prop_files = [build_prop_ref for build_prop_ref in firmware.build_prop_file_id_list]
                        detected_vendor = detect_vendor_by_build_prop(build_prop_files)
                        
                        if detected_vendor != "Unknown" and detected_vendor != firmware.os_vendor:
                            self.stdout.write(
                                f'[DRY RUN] Would update firmware {firmware.id}: '
                                f'"{firmware.os_vendor}" -> "{detected_vendor}" '
                                f'(file: {firmware.original_filename})'
                            )
                            updated_count += 1
                        else:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'[DRY RUN] No change for firmware {firmware.id}: '
                                    f'current="{firmware.os_vendor}", detected="{detected_vendor}" '
                                    f'(file: {firmware.original_filename})'
                                )
                            )
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f'[DRY RUN] No build.prop files for firmware {firmware.id} '
                                f'(file: {firmware.original_filename})'
                            )
                        )
                
                self.stdout.write(
                    self.style.SUCCESS(f'[DRY RUN] Would update {updated_count} firmware records')
                )
            else:
                # Actually update firmware
                if firmware_ids:
                    updated_count = update_firmware_vendor_by_build_prop(firmware_ids)
                elif update_all:
                    # For --all flag, we need to implement a special case
                    all_firmware = AndroidFirmware.objects()
                    all_ids = [str(fw.id) for fw in all_firmware]
                    updated_count = update_firmware_vendor_by_build_prop(all_ids)
                else:
                    updated_count = update_firmware_vendor_by_build_prop()

                self.stdout.write(
                    self.style.SUCCESS(f'Successfully updated vendor for {updated_count} firmware records')
                )

        except Exception as e:
            raise CommandError(f'Error updating firmware vendor information: {str(e)}')