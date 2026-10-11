# AGENTS.md — карта проекта RedmiBook TM2309

Этот файл — **короткий маршрутизатор контекста**, не технический отчёт и не журнал текущих задач.

## Обязательный минимум при входе в задачу

1. Этот `AGENTS.md`.
2. [Цель, этап и границы](docs/RESEARCH_SCOPE.md).
3. **[Issue #2 — единственное актуальное состояние, проценты и чек-листы](https://github.com/KobaProduction/redmibook-firmware/issues/2)**.

При команде «освежи/перечитай обязательный контекст» **дополнительно действительно открыть** [правила анализа](docs/ANALYSIS_PROCESS.md), [термины](docs/TERMS.md), корневые `AGENTS.md` / `README.md` [ai-agent-workflow](https://github.com/ArthurKoba/ai-agent-workflow), его [единый навык обратного анализа](https://github.com/ArthurKoba/ai-agent-workflow/blob/main/skills/reverse-analysis.md) и [протокол отчётности](https://github.com/ArthurKoba/ai-agent-workflow/blob/main/docs/REPORTING_PROTOCOL.md). При работе непосредственно с Analysis использовать раздел **Persistent Analysis project and worker lifecycle** в `skills/reverse-analysis.md`; для Java/GhidraScript — раздел **Java/GhidraScript analysis and monitored jobs** того же файла. При согласованной Git-фиксации — git-workflow/роль Writer и Reviewer. Не загружать их заново механически после каждого шага.

## Источники истины: не смешивать

- **Канонический Analysis** `RedmiBook_TM2309_Firmware_Analysis`, ID `ghp_2bf17493ef188f564a68d8ae`: единственная текущая техническая истина о BIOS/EC — функции, регистры, структуры, протоколы, адреса, переходы, гипотезы, трассы, подтверждения и противоречия. Результаты оформлять/именовать и сохранять **там**.
- **GitHub `main`**: цель, правила, навигация, общий состав платформы и ссылки, но **не** параллельный подробный каталог регистров и алгоритмов.
- **[Issue #2](https://github.com/KobaProduction/redmibook-firmware/issues/2)**: единственная редактируемая рабочая задача, приоритеты, проценты, блокировки и чек-листы.
- **Замороженный архив**: прежние исследовательские Git-ветки заменены сохраняемыми исходными снимками в подключённом пространстве Files: `projects/redmibook-firmware/legacy-evidence/README.md`. Это источник для адресной проверки, **не** действующая техническая истина. Новые доказательства вносятся только в Analysis.

## Куда идти за направлением

[Карта областей](docs/DOMAINS.md) → небольшая специализированная карта → соответствующие сохранённые программы **Analysis**. Для простого раздела допускается прямая ссылка на документ; если карта становится большой либо смешивает независимые области, разделить её и обновить ссылки здесь или в родительской карте.

- Разгон, частоты, undervolt, память, матрица → [карта](docs/domains/performance-voltage.md).
- Батарея, питание, CPU power limits, USB-C/Thunderbolt → [карта](docs/domains/energy-usb.md).
- Температуры, обороты, нагрузка, расход энергии → [карта](docs/domains/telemetry.md).
- Вентиляторы, режимы, микрофон, клавиатура, дисплей, пробуждение → [карта](docs/domains/platform-controls.md).
- [Происхождение прошивки и Analysis](docs/ARTIFACTS.md) — только общие сведения о корпусе.

## Открытые исходники для реверса A0A

При восстановлении **стандартных UEFI/PI/SMM-модулей** TM2309 сначала проверь соответствующие исходники, прежде чем вручную разбирать известную библиотечную реализацию. Основные ориентиры: [TianoCore EDK II](https://github.com/tianocore/edk2/tree/edk2-stable202405), [edk2-platforms](https://github.com/tianocore/edk2-platforms), [coreboot](https://github.com/coreboot/coreboot) и [Intel FSP](https://github.com/intel/FSP) (FSP может содержать только бинарные компоненты). Для уже найденных соответствий A0A есть прямые ссылки на [SmiHandlerProfile.c](https://github.com/tianocore/edk2/blob/edk2-stable202405/MdeModulePkg/Core/PiSmmCore/SmiHandlerProfile.c), [SmmSwDispatch2.h](https://github.com/tianocore/edk2/blob/edk2-stable202405/MdePkg/Include/Protocol/SmmSwDispatch2.h), [FirmwarePerformancePei.c](https://github.com/tianocore/edk2/blob/edk2-stable202405/MdeModulePkg/Universal/Acpi/FirmwarePerformanceDataTablePei/FirmwarePerformancePei.c) и [Metronome.c](https://github.com/tianocore/edk2/blob/edk2-stable202405/MdeModulePkg/Universal/Metronome/Metronome.c).

Ищи соответствия по **FFS FILE_GUID, Protocol/PPI GUID, INF и именам модулей, строкам, константам и структуре вызовов/CFG**. GUID или название — только кандидат: версии, компиляторы, архитектура, оптимизация, ABI и OEM-изменения могут существенно отличаться. Подтверждай совпадение **по каждой функции** в заводском коде; не переносить всю таблицу имён, сигнатур или смещения без проверки.

Найденный референс фиксируй **в каноническом Analysis**, не в параллельном отчёте: на входе модуля bookmark `EDK2_REFERENCE_MODULE_PARTIAL` со ссылкой на конкретный исходник/версию и границами соответствия; на проверенных функциях — `EDK2_SOURCE_FUNCTION_CONFIRMED`, корректные имена и доказательства. Сохранить и перечитать. Эта практика помогает разбирать нужные направления, но **не требует массово импортировать, собирать или переанализировать все модули**.

## Рабочие ограничения

Текущий этап — **анализ заводской прошивки для обнаружения переносимых интерфейсов ОС (Windows И Linux)**, а не реализация приложения или собственного BIOS. Выбирать слабо раскрытую, но полезную область; использовать адресную трассировку только настолько, насколько необходимо для аппаратной связи/OS-доступности. Статус каждого семантического вывода по-русски: **Подтверждено / Вероятно / Неизвестно / Противоречие**. Не считать меню BIOS, успешный ответ или совпадение чисел доказательством аппаратного исполнения.

**Без отдельного явного поручения пользователя на конкретную фиксацию: не делать Git-коммитов, push, PR, merge или удаление веток.** В обычном проходе меняются Analysis и Issue. При одобренной публикации: Writer → PR → независимый Reviewer → `main`; не обходить резерв `main`. В чате показывать преимущественно изменившийся прогресс `было → стало`, открытия и реальные препятствия.
