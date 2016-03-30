tags = function (query, size, skip) {
	var data = [];
	var cor = db.Tags.find(query).limit(size).skip(skip);
	cor.forEach(function(tag){
		image = db.Image.findOne({"_id":tag.digest});
		if (image)
		{
			tag['size'] = image['size'];
			tag['user_id'] = image['user_id'];
			tag['pull_num'] = image['pull_num'];
		}
		repo = db.Repository.findOne({"_id":tag.repository});
		if (repo)
		{
			tag['permission'] = repo['permission'];
		}
		data.push(tag);
	});

	return {"result":0, "content":data};
}
