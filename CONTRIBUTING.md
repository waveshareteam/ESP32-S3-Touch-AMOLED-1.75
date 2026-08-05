# Contributing

[中文](CONTRIBUTING_ZH.md)

Thanks for helping improve this repository.

## Workflow

1. Open an issue for behavioral bugs or compatibility problems when the root cause is not already clear.
2. Keep changes scoped to one topic.
3. Update documentation when paths, supported versions, or user workflows change.
4. Let CI validate source builds for ESP-IDF and Arduino examples.

## Examples And Firmware

- First-party ESP-IDF projects live directly under `examples/esp-idf/`.
- First-party Arduino sketches live directly under `examples/arduino/`.
- Bundled-library examples are dependencies or upstream samples and are not product CI targets.
- `firmware/brookesia/` is a separately maintained source project outside example discovery.
- A factory or recovery binary must be replaced only with matching build provenance, checksums,
  delivery documentation, and hardware-validation evidence.

## Documentation

Keep the English and Chinese entry documents synchronized. When changing user-visible hardware
specifications, commands, links, firmware filenames, checksums, or support instructions, update the
corresponding language document in the same pull request.

## Pull Requests

Pull requests should include:

- A concise summary of the change.
- The affected example, documentation, firmware, or workflow paths.
- The CI jobs or validation performed.
- Hardware validation performed, or a clear reason it is not applicable.
- Firmware or SD-card artifact impact, including updated checksums when applicable.
- Any known limitations or follow-up work.

Do not include local machine paths, usernames, tool installation directories, Wi-Fi credentials,
tokens, private keys, private chat or media content, or other host-specific or sensitive details in
public repository text, logs, commits, or artifacts. Include only the minimum diagnostic output
needed to review the change, and redact it before publishing.
