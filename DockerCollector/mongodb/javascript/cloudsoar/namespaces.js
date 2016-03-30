namespaces = function (query, size, skip) {
	var data = [];
	var cor = db.Namespace.find(query).limit(size).skip(skip);
	cor.forEach(function(nspc){
		nspc['repo_num'] = db.Repository.count({'namespace':nspc._id});
		data.push(nspc);
	});

	return {"result":0, "content":data};
}
