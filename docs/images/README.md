# Documentation Images

This folder contains screenshots and images for the documentation guides.

## File Naming Convention
- Use descriptive names with hyphens: `elastic-beanstalk-create-app.png`
- Include step numbers for sequential screenshots: `01-create-application.png`
- Use consistent prefixes for different guides:
  - `eb-` for Elastic Beanstalk screenshots
  - `iam-` for IAM role screenshots
  - `bedrock-` for Bedrock model access screenshots
  - `app-` for application interface screenshots

## Image Guidelines
- Use PNG format for screenshots
- Crop to show relevant sections only
- Highlight important buttons/fields with red boxes or arrows
- Keep file sizes reasonable (< 500KB per image)
- Use consistent browser/theme for professional appearance

## Usage in Documentation
Reference images using relative paths:
```markdown
![Description](images/filename.png)
```