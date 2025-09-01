"""API responses to test against."""

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

BASIC_SEARCH_RESPONSE = {
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

MULTI_MODEL_SEARCH_RESPONSE = {
    'results': [
        {
            'score': 1.0,
            'sheet': 'TestSheet',
            'row_id': 1,
            'fields': {'Name': 'Test Item', 'Level': 50},
        },
        {
            'score': 0.3333,
            'sheet': 'OtherSheet',
            'row_id': 7,
            'fields': {'Name': 'Other Item', 'Field@as(raw)': 14},
        },
    ],
    'next': None,
}

MULTI_MODEL_SEARCH_RESPONSE_BROKEN = {
    'results': [
        {
            'score': 1.0,
            'sheet': 'TestSheet',
            'row_id': 1,
            'fields': {'Name': 'Test Item', 'Level': 50},
        },
        {
            'score': 0.3333,
            'sheet': 'OtherSheet',
            'row_id': 7,
            'fields': {'Name': 'Other Item'},
        },
        {
            'score': 0.512,
            'sheet': 'TestSheet',
            'row_id': 83,
            'fields': {'Name': 'Other Test Item', 'Level': 88},
        },
    ]
}

SEARCH_RESPONSE_PAGE_1 = {
    'results': [
        {
            'score': 1.0,
            'sheet': 'TestSheet',
            'row_id': 23,
            'fields': {'Name': 'Test Item', 'Level': 89},
        }
    ],
    'next': '28433b5b-7860-4395-88df-17c75c173a7c',
}
SEARCH_RESPONSE_PAGE_2 = {
    'results': [
        {
            'score': 0.899,
            'sheet': 'TestSheet',
            'row_id': 212,
            'fields': {'Name': 'Another Test Item', 'Level': 50},
        }
    ],
    'next': None,
}

SHEET_ROW_RESPONSE = {'row_id': 1, 'fields': {'Name': 'Test Item', 'Level': 50}}
SHEET_ROWS_RESPONSE = {
    'rows': [
        {
            'row_id': 1,
            'fields': {'Name': 'Test Item', 'Level': 50},
        },
        {
            'row_id': 2,
            'fields': {'Name': 'Second Item', 'Level': 44},
        },
        {
            'row_id': 3,
            'fields': {'Name': 'Final Item', 'Level': 999},
        },
    ]
}
