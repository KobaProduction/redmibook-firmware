# Карта: энергия, батарея, USB и Thunderbolt

**Живой прогресс — [Issue #2](https://github.com/KobaProduction/redmibook-firmware/issues/2), раздел 2.**

Область: ограничение заряда батареи, состояние и здоровье аккумулятора, адаптер питания, длительные/кратковременные лимиты мощности процессора, cTDP, USB-зарядка и её порог, USB-C/Thunderbolt/USB Power Delivery.

Искать пути чтения/управления из **Windows и Linux** отдельно от загрузочных действий BIOS. Сначала API ОС и доступные политики, затем ACPI/UEFI runtime, вендорские WMI/SMM, EC-поставщик и аппаратные ограничения. Успешное сохранение настройки не равно применению. Изолировать опасные записи в firmware/EC/MSR; пока только статический анализ.

Маршрутизация Analysis: `AutoBackupSCUSetting`/конфигурационные переменные, `HQDxeService`/EC, `OemWMISmmCallback`, `OemODMSmmServiceDriver`, `DxeCpuPowerManagement`, `ThermalSmm`. USB-C/Thunderbolt/PD — отдельная практически не начатая разведка; не приписывать им возможности только по наличию порта.
