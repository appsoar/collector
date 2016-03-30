repositories = function (query, size, skip) {

	var extent = function(srcObj, tarObj){
		for(var p in srcObj){
			if(typeof(srcObj[p])=="function"){ 
				continue;
			}
			else{
				tarObj[p] = srcObj[p];
			}
		}
		return tarObj;
	}

	var GetTags = function(repo_id){
        
        arr = []
        var corsur = db.Tags.find({'repository':repo_id})
        corsur.forEach(function(tag){
			image = db.Image.findOne({"_id":tag.digest});
			if (image)
			{
				tag['size'] = image['size'];
				tag['user_id'] = image['user_id'];
				tag['pull_num'] = image['pull_num'];
			}
            arr.push(tag);
        });
        return arr;
    }

	var data = [];
	var cor = db.Repository.find(query).limit(size).skip(skip);
	cor.forEach(function(repo){
		repo['tags'] = GetTags(repo._id);
		data.push(repo);
	});

	return {"result":0, "content":data};
}
