from flask_restx import fields, Model

test = Model('test', {
    'id': fields.String(required=True, description='The unique identifier of a blog post'),
    'title': fields.String(required=True, description='Article title'),
    'body': fields.String(required=True, description='Article content'),
    'status': fields.String(required=True, enum=['DRAFT', 'PUBLISHED', 'DELETED']),
    'pub_date': fields.DateTime(required=True)
})

object_id_list = Model('object_id_list', {
    'object_id_list': fields.List(fields.String(required=True),
                                   required=True,
                                   description='A list of object identifiers',
                                   example=["5eeddfe82ea100614bd8327b", "5eeddff52ea100614bd8327c"])
})

fuzzy_hash_compare_model = Model('fuzzy_hash_compare_model', {
    'hash_a': fields.String(required=True, description='Fuzzy Hash',
                            example="25165824:FlZB/ydRAx7V49SzGlnap0sXeiqzhStZ7CSBTgIEbEriDwwuc://yTSS20sXreStkS5gvYrPwuc"),
    'hash_b': fields.String(required=True, description='Fuzzy Hash',
                            example="25165824:2nToh2nV+n4l6DTTnEM+Y7q+ZXAnKuKhZ9JqbEI0O+g1/:2xk4l6DHEMxXeKDnJqbBR+g1/"),
})

virustotal_api_key_model = Model('virustotal_api_key_model', {
    'api_key': fields.String(required=True, description='Virustotal API Key',
                             example="bc59dc11a063c7e117ca542c65189e032084ccbe31d3e75ab560a1c89a45a832")
})