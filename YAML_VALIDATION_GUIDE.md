# YAML Validation Examples

## ✅ Valid YAML
```yaml
appId: com.example.app
---
- launchApp:
    clearState: true
- tapOn: "Login"
- inputText: "user@example.com"
```

## ❌ Common YAML Errors

### 1. Missing Dash (-)
```yaml
appId: com.example.app
---
tapOn: "Login"  ❌ Missing dash!
```
**Fix:**
```yaml
- tapOn: "Login"  ✅
```

### 2. Standalone Text (No # or -)
```yaml
- tapOn: "Button"

Click the next button  ❌ Invalid!

- tapOn: "Next"
```
**Fix:**
```yaml
- tapOn: "Button"

# Click the next button  ✅ Add # for comments

- tapOn: "Next"
```

### 3. Missing Colon (:)
```yaml
- tapOn
    id "button"  ❌ Missing colon after id
```
**Fix:**
```yaml
- tapOn:
    id: "button"  ✅
```

### 4. Incorrect Indentation
```yaml
- tapOn:
  id: "button"  ❌ Should be 4 spaces
```
**Fix:**
```yaml
- tapOn:
    id: "button"  ✅ 4 spaces
```

### 5. Unquoted Special Characters
```yaml
- tapOn: Filter: All  ❌ Colon needs quotes
```
**Fix:**
```yaml
- tapOn: "Filter: All"  ✅
```

## 💡 Tips

1. **Always start commands with `-`**
2. **Use `#` for comments**
3. **Use 4 spaces for indentation** (not tabs)
4. **Quote text with special characters** (`:`, `"`, `{`, `}`, etc.)
5. **Check the OUTPUT panel** for detailed error messages
