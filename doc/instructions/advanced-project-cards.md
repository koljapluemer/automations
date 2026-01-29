Let's extend project cards stuff a little.
The .md files also may have metadata like 

```
archived: true
```


In that case, transfer this boolean prop to the generated JSON also.
In the same way, they may have `showcase: true`, which please also just transfer to the JSON.

They also may have

```
failed: was just too annoying
```

In that case, transfer to JSON; note that this is a string

They also may have

```
links:
  Website: https://inspo.koljapluemer.com/versions/collage/main
  Legacy-Repository: https://github.com/koljapluemer/inspirationbot
  New-Repository: https://github.com/koljapluemer/inspiration-bot
```

Also transfer this, note how it's a sort of nested dictionary. Replace "-" within the key with " " So it can be used as a nice link title

They also may have, not in their yaml frontmatter, but just in their body, a description like:

```
- **A [[perceptual exposure]] binary-choice UI [[◊ learning tool|learning tool]] for recognizing birds**
```

- find this description by looking for the first line starting with exactly "- **"
- strip the Obsidian link syntax and the bold and the bullet point elegantly, noting also the alias syntax, so that you get simply:

```
A perceptual exposure binary-choice UI learning tool for recognizing birds
```

Render this on the png card below the header in a smaller font and left-centered, and transfer to the JSON as property `description`
