VERSIONS_RESPONSE = {
    'versions': [
        {'names': ['7.3x1']},
        {'names': ['latest']},
    ]
}

SHEETS_RESPONSE = {
    'sheets': [
        {'name': 'Item'},
        {'name': 'ContentFinderCondition'},
        {'name': 'Quest'},
    ]
}

SEARCH_RESPONSE = {
    'results': [
        {
            'score': 1.0,
            'sheet': 'TestSheet',
            'row_id': 1,
            'fields': {'Name': 'Test Item', 'Level': 50},
        }
    ],
    'next': None,
}

SHEET_ROW_RESPONSE = {'row_id': 1, 'fields': {'Name': 'Test Item', 'Level': 50}}
