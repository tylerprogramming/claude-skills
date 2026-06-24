# Kie.ai model reference (for the /kie-* skills)

Verified model ids + input schemas captured from docs.kie.ai. Skills route through
the shared `_kie/kie_client.py` (unified `/jobs/createTask`) EXCEPT Veo, which uses
its own `/api/v1/veo/generate` endpoint.

## Unified jobs API (most models)
POST https://api.kie.ai/api/v1/jobs/createTask  body `{"model": id, "input": {...}}`
GET  https://api.kie.ai/api/v1/jobs/recordInfo?taskId=...  -> resultJson.resultUrls

### Seedance video (ByteDance)
- `bytedance/seedance-2` — t2v+i2v multimodal. input: prompt, first_frame_url?, last_frame_url?, reference_image_urls?[≤9], resolution(480p|720p|1080p=720), aspect_ratio(1:1|4:3|3:4|16:9|9:16|21:9|adaptive=16:9), duration(int 4-15=5), generate_audio(bool=true)
- `bytedance/seedance-2-fast` — same, resolution 480p|720p only
- `bytedance/seedance-1.5-pro` — t2v+i2v. input: prompt, aspect_ratio(req), duration("4"|"8"|"12"), input_urls?[0-2], resolution(480p|720p|1080p=720), generate_audio(bool=false), fixed_lens?
- `bytedance/v1-pro-text-to-video` — input: prompt, aspect_ratio(21:9|16:9|4:3|1:1|3:4|9:16=16:9), resolution(480p|720p|1080p=720), duration("5"|"10"), camera_fixed?, seed?
- `bytedance/v1-pro-image-to-video` — input: prompt, image_url, resolution, duration("5"|"10"), camera_fixed?, seed?
- `bytedance/v1-pro-fast-image-to-video` — resolution 720p|1080p only
- `bytedance/v1-lite-text-to-video` / `bytedance/v1-lite-image-to-video` — input similar; lite i2v adds end_image_url?

### Kling video (Kuaishou)
- `kling-2.6/text-to-video` — input: prompt(≤1000), sound(bool req), aspect_ratio(1:1|16:9|9:16), duration("5"|"10")
- `kling-2.6/image-to-video` — input: prompt, image_urls[max1], sound(bool), duration("5"|"10")
- `kling-3.0/video` — input: prompt OR multi_prompt[], sound(bool=false), duration("3".."15"=5), aspect_ratio(16:9|9:16|1:1), mode(std|pro|4K=pro), multi_shots(bool=false), image_urls?, kling_elements?
- `kling/v2-1-master-text-to-video` — input: prompt(≤5000), duration("5"|"10"), aspect_ratio, negative_prompt?, cfg_scale(0-1=0.5)
- `kling/v2-1-pro` — i2v. input: prompt, image_url, duration("5"|"10"), negative_prompt?, cfg_scale?, tail_image_url?

### Wan video (Alibaba)
- `wan/2-7-text-to-video` — input: prompt, negative_prompt?, audio_url?, resolution(720p|1080p=1080p), ratio(16:9|9:16|1:1|4:3|3:4), duration(int 2-15=5), prompt_extend(bool=true), watermark(bool=false), seed?  [NOTE field is `ratio` not aspect_ratio]
- `wan/2-7-image-to-video` — input: prompt, first_frame_url?, last_frame_url?, first_clip_url?, driving_audio_url?, resolution, duration(2-15=5), prompt_extend, watermark, seed?
- `wan/2-6-image-to-video` — input: prompt, image_urls[max1], duration("5"|"10"|"15"), resolution(720p|1080p=1080p)
- `wan/2-5-text-to-video` — input: prompt(≤800), duration("5"|"10"), aspect_ratio(16:9|9:16|1:1), resolution(720p|1080p), negative_prompt?, enable_prompt_expansion?, seed?

### Seedream image (ByteDance)
- `seedream/4.5-text-to-image` — input: prompt(≤3000), aspect_ratio(1:1|4:3|3:4|16:9|9:16|2:3|3:2|21:9), quality(basic=2K|high=4K)
- `seedream/4.5-edit` — i2i. input: prompt, image_urls[≤14], aspect_ratio, quality
- `seedream/5-lite-text-to-image` — input: prompt(3-3000), aspect_ratio, quality(basic|high)

### Nano Banana image
- `google/nano-banana` — t2i. input: prompt(≤5000), output_format(png|jpeg), aspect_ratio(1:1|9:16|16:9|3:4|4:3|3:2|2:3|5:4|4:5|21:9|auto)
- `google/nano-banana-edit` — edit. input: prompt, image_urls[≤10], output_format, aspect_ratio
- `nano-banana-2` — t2i+edit. input: prompt(≤20000), image_input?[≤14], aspect_ratio(+1:4,1:8,4:1,8:1...=auto), resolution(1K|2K|4K), output_format(jpg|png)
- `nano-banana-pro` — t2i+edit. input: prompt(≤10000), image_input?[≤8], aspect_ratio, resolution(1K|2K|4K), output_format(png|jpg)

### GPT Image 2 (OpenAI)
- `gpt-image-2-text-to-image` — t2i. input: prompt(≤20000), aspect_ratio(auto|1:1|3:2|2:3|4:3|3:4|5:4|4:5|16:9|9:16|2:1|1:2|3:1|1:3|21:9|9:21=auto), resolution(1K|2K|4K). Output PNG.
- `gpt-image-2-image-to-image` — edit. input: prompt, input_urls[≤16], aspect_ratio, resolution. Output PNG.
- Constraints: 5:4 & 4:5 are 1K-only; 1:1 can't go 4K; `auto` aspect ratio limited to 1K.

## Dedicated endpoint — Veo (Google)
POST https://api.kie.ai/api/v1/veo/generate  (flat camelCase body)
GET  https://api.kie.ai/api/v1/veo/record-info?taskId=...
- model: `veo3` (3.1 Quality) | `veo3_fast` (default) | `veo3_lite`
- body: prompt(req), imageUrls?[1-3], aspectRatio(16:9|9:16|Auto=16:9), resolution(720p|1080p|4k=720p), duration(4|6|8=8), enableTranslation?, watermark?, callBackUrl?
- generationType auto-detected (TEXT_2_VIDEO | FIRST_AND_LAST_FRAMES_2_VIDEO | REFERENCE_2_VIDEO)

## NOT on Kie.ai: Pixverse, Vidu, Luma, Hunyuan.
## Pricing: not in docs — pull live from kie.ai Market/Playground.
