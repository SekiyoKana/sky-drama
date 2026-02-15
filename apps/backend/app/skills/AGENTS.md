# AI SKILLS KNOWLEDGE BASE

## OVERVIEW
Modular AI generation logic. Each subdirectory represents a specific generation capability.

## STRUCTURE
```
apps/backend/app/skills/
├── knowledge/                   # Shared prompts/context?
├── short_video_screenwriter/    # Script generation
├── short_video_storyboard_maker/# Visual planning
├── short_video_prompt_engineer/ # SD/Midjourney prompt refinement
└── loader.py                    # Dynamic loading logic (presumed)
```

## PATTERNS
- **Separation**: Keep prompt engineering separate from asset generation.
- **Streaming**: Long-running tasks should support streaming responses (SSE) if possible.
- **Context**: Skills often share `project_id` / `episode_id` context.

## ADDING A SKILL
1. Create new directory `apps/backend/app/skills/<new_skill>`.
2. Implement core logic.
3. Expose via `ai` router in `apps/backend/app/api/v1/endpoints/ai.py`.
