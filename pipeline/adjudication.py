"""Restore exact source IDs/quotes from explicit short response references."""
from .core import validate

def restore(output,batch,accept_original_ids=False):
    labels=output.get('records')
    if not isinstance(labels,list):raise ValueError('Missing records')
    refs={'R'+str(i+1):row for i,row in enumerate(batch)}
    if accept_original_ids:
        for row in batch:
            if row['id'] in refs and refs[row['id']]['id']!=row['id']:raise ValueError('Ambiguous response reference')
            refs[row['id']]=row
    restored=[]
    for label in labels:
        if not isinstance(label,dict) or label.get('review_id') not in refs:
            raise ValueError('Unknown response reference')
        row=refs[label['review_id']]
        restored.append({**label,'review_id':row['id'],'evidence_quote':row['text']})
    return validate(restored,batch)
